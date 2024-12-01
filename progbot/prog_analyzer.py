import decimal
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import discord
from data import DEFAULT_ENCOUNTER_ID, Encounter, EncounterId, encounter_by_id
from discord import app_commands
from discord.ext import commands
from fflogsapi import FFLogsClient
from gql.transport.requests import log as requests_logger
from queries import CAST_EVENTS_INNER_QUERY, FIGHT_DATA_INNER_QUERY, REPORT_QUERY
from utility import get_human_readable_timedelta

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
requests_logger.setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib").setLevel(logging.WARNING)


@dataclass
class ProgSummaryItem:
    description: str
    fight_ids: list[int]
    total_duration: decimal

    def wipe_count(self) -> int:
        return len(self.fight_ids)


class EncounterContext:
    encounter: Encounter
    report_code: str
    log_url: str
    log_date: datetime
    fight_duration_sum: decimal
    fights_by_id: dict[int, dict]
    prog_summary: list[ProgSummaryItem]


class ProgAnalyzer(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        fflogs_api_client_id: str,
        fflogs_api_client_secret: str,
    ) -> None:
        super().__init__()

        self.bot = bot
        self.fflogs_client = FFLogsClient(
            fflogs_api_client_id,
            fflogs_api_client_secret,
            cache_expiry=3000,  # 5 mins
        )

    def _extract_report_code(self, log_url: str) -> str | None:
        match = re.search(r"fflogs\.com\/reports\/(?P<slug>[a-zA-Z0-9]+)", log_url)
        return match.group("slug") if match else None

    def _fetch_report_by_code(self, encounter_id, report_code) -> dict[str, dict]:
        result = self.fflogs_client.q(
            REPORT_QUERY.format(
                reportCode=report_code,
                innerQuery=FIGHT_DATA_INNER_QUERY.format(
                    encounterID=encounter_id.value
                ),
            )
        )["reportData"]["report"]

        # Append some useful data
        for fight_dict in result["fights"]:
            fight_dict["duration"] = fight_dict["endTime"] - fight_dict["startTime"]

        return result

    def _get_casts_query(
        self, report_code: str, fight_ids: list[int], start_time: int, end_time: int
    ) -> str:
        return REPORT_QUERY.format(
            reportCode=report_code,
            innerQuery=CAST_EVENTS_INNER_QUERY.format(
                fightIDs=fight_ids,
                startTime=start_time,
                endTime=end_time,
            ),
        )

    def _fetch_casts(
        self, report_code, fight_ids, start_time, end_time
    ) -> list[dict[str, Any]]:
        result = self.fflogs_client.q(
            self._get_casts_query(
                report_code=report_code,
                fight_ids=fight_ids,
                start_time=start_time,
                end_time=end_time,
            )
        )
        result = result["reportData"]["report"]["events"]
        cast_data = result["data"]

        # Continue to fetch if there are more pages.
        next_page_timestamp = result["nextPageTimestamp"]
        while next_page_timestamp:
            result = self.fflogs_client.q(
                self._get_casts_query(
                    report_code=report_code,
                    fight_ids=fight_ids,
                    start_time=next_page_timestamp,
                    end_time=end_time,
                )
            )
            result = result["reportData"]["report"]["events"]
            cast_data += result["data"]
            next_page_timestamp = result["nextPageTimestamp"]

        return cast_data

    @app_commands.command()
    @app_commands.describe(log_url="The URL of the fflogs report.")
    @app_commands.describe(
        encounter_id="The id of the encounter.",
    )
    async def prog(
        self,
        interaction: discord.Interaction,
        log_url: str,
        encounter_id: Optional[EncounterId] = None,
    ) -> None:
        logger.debug(f"Received prog command for {log_url}")

        ctx = EncounterContext()
        ctx.encounter = encounter_by_id[encounter_id or DEFAULT_ENCOUNTER_ID]
        ctx.log_url = log_url

        await interaction.response.defer(ephemeral=True)

        ctx.report_code = self._extract_report_code(log_url)
        if not ctx.report_code:
            await interaction.followup.send(
                content="The URL must point to a valid fflogs report.",
                ephemeral=True,
            )
            return

        await interaction.edit_original_response(
            content="Fetching report from fflogs..."
        )

        report = self._fetch_report_by_code(ctx.encounter.id, ctx.report_code)

        ctx.log_date = datetime.fromtimestamp(report["startTime"] / 1000)
        ctx.fight_duration_sum = sum(d["duration"] for d in report["fights"])
        ctx.fights_by_id = {d["id"]: d for d in report["fights"]}

        await interaction.edit_original_response(
            content="Done! Parsing prog data from fflogs..."
        )

        # Implicitly sorted by timestamp and fightID by the fflogs API
        casts = self._fetch_casts(
            ctx.report_code,
            list(ctx.fights_by_id.keys()),
            report["fights"][0]["startTime"],
            report["fights"][-1]["endTime"],
        )

        relevant_cast_ids = ctx.encounter.prog_indicating_cast_ids()
        casts = list(
            filter(
                # Filter out begin casts and casts we aren't interested in
                lambda d: d["type"] == "cast"
                and d["abilityGameID"] in relevant_cast_ids,
                casts,
            )
        )
        cast_counts_by_fight_and_ability = defaultdict(int)
        latest_cast_id_by_fight: dict[str, int] = {}
        for cast in casts:
            latest_cast_id_by_fight[cast["fight"]] = cast["abilityGameID"]
            cast_counts_by_fight_and_ability[
                (cast["fight"], cast["abilityGameID"])
            ] += 1

        fight_ids_by_prog = defaultdict(list[int])
        for fight_id in ctx.fights_by_id:
            latest_cast_id = latest_cast_id_by_fight[fight_id]
            pi = ctx.encounter.get_prog_indicator_by_cast_and_count(
                latest_cast_id,
                cast_counts_by_fight_and_ability[(fight_id, latest_cast_id)],
            )
            fight_ids_by_prog[pi].append(fight_id)

        ctx.prog_summary = [
            ProgSummaryItem(
                pi.description,
                fight_ids_by_prog[pi],
                sum(
                    ctx.fights_by_id[fight_id]["duration"]
                    for fight_id in fight_ids_by_prog[pi]
                ),
            )
            for pi in ctx.encounter.prog_indicators
            if fight_ids_by_prog[pi]
        ]

        await interaction.edit_original_response(
            content="Done! Constructing message..."
        )
        await interaction.delete_original_response()
        await interaction.channel.send(
            embed=self._construct_response_embed(ctx),
        )

    @prog.error
    async def on_command_error(self, interaction: discord.Interaction, error) -> None:
        logger.exception(error)
        await interaction.edit_original_response(
            content="Ran into an error processing the command. Double check your URL and command parameters.",
        )

    def _construct_response_embed(self, ctx: EncounterContext) -> discord.Embed:
        message_embed = discord.Embed(
            title=f"Summary of Wipes for {ctx.encounter.name}",
            url=ctx.log_url,
            color=0x82878F,
            timestamp=ctx.log_date,
        )

        for item in ctx.prog_summary:
            total_duration_ms = sum(
                ctx.fights_by_id[fid]["duration"] for fid in item.fight_ids
            )
            percentage_of_wipes = 100 * total_duration_ms / ctx.fight_duration_sum
            wipe_duration_str = get_human_readable_timedelta(
                timedelta(milliseconds=total_duration_ms)
            )

            field_value = (
                f"**{percentage_of_wipes:.1f}%** - {wipe_duration_str} in {item.wipe_count()} wipe"
                + ("s" if item.wipe_count() > 1 else "")
            )
            message_embed.add_field(
                name=discord.utils.escape_markdown(item.description, as_needed=True),
                value=field_value,
                inline=False,
            )

        message_embed.set_footer(text="Log timestamp")
        return message_embed

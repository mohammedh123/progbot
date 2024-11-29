REPORT_QUERY = """
query {{
    reportData {{
        report(code: "{reportCode}") {{
            {innerQuery}
            startTime
            endTime
        }}
    }}
}}
"""

CAST_EVENTS_INNER_QUERY = """
events(
    fightIDs: {fightIDs}
    dataType: Casts
    hostilityType: Enemies
    startTime: {startTime}
    endTime: {endTime}
    limit: 10000
) {{
    data
    nextPageTimestamp
}}
"""

FIGHT_DATA_INNER_QUERY = """
fights(encounterID: {encounterID}, killType: Wipes) {{
    id
    startTime
    endTime
}}
"""

def get_human_readable_timedelta(delta) -> str:
    total_seconds = int(delta.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)

    minute_part = (
        f"{minutes} minute{'s' if minutes != 1 else ''}" if minutes > 0 else ""
    )
    second_part = (
        f"{seconds} second{'s' if seconds != 1 else ''}" if seconds > 0 else ""
    )

    if minute_part and second_part:
        return f"{minute_part} and {second_part}"
    elif minute_part:
        return minute_part
    elif second_part:
        return second_part
    else:
        return "0 seconds"

from time import localtime
from lib import logging


def _get_timestamp():
    t = localtime()
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )


def log_message(message, log_file, max_lines=100, enable=False):
    timestamp = _get_timestamp()
    log_entry = "[{}] {}\n".format(timestamp, message)

    # Print the log entry
    print(log_file, log_entry)
    if not enable:
        return log_entry

    # Read the existing log file content
    existing_lines = []
    try:
        with open(log_file, "r") as f:
            existing_lines = f.readlines()
    except OSError:
        pass

    # Ensure the log file does not exceed the maximum number of lines
    if len(existing_lines) >= max_lines:
        # Calculate the number of lines to remove (25% of the oldest lines)
        lines_to_remove = len(existing_lines) // 4

        # Remove the oldest lines
        existing_lines = existing_lines[lines_to_remove:]

    # Append the new log entry to the existing content
    existing_lines.append(log_entry)

    # Write the updated content back to the log file
    with open(log_file, "w") as f:
        for line in existing_lines:
            f.write(line)

    return log_entry

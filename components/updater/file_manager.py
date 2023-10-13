from components.logger import log_message
import ujson


def get_local_version(file_location, log_file):
    try:
        with open(file_location, "r") as file:
            json_data = file.read()

            parsed_json = ujson.loads(json_data)
            if parsed_json and parsed_json["version"]:
                log_message("Local Version: " + str(parsed_json["version"]), log_file)
                return parsed_json["version"]
            return None

    except OSError as e:
        print("Error reading JSON file:", e)
        return None


def get_version(esp_process, url, port, version_file, log_file, files_list):
    matches = [match for match in files_list if version_file in match]
    if len(matches) > 0:
        (header, body, status_code) = esp_process.get_url_response(
            url + version_file, port
        )
        if body == None or not body["version"]:
            log_message("No remote version body found", log_file)
            return False

        log_message("Remote Version: " + str(body["version"]), log_file)
        local_version = get_local_version(version_file, log_file)
        if local_version is not None and body["version"] > local_version:
            return True

    return False

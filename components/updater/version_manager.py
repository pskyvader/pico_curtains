from lib.logging import getLogger, handlers, StreamHandler
import ujson

log_file = "get_version.txt"
logger_version_manager = getLogger("get_version")
logger_version_manager.addHandler(handlers.RotatingFileHandler(log_file))
logger_version_manager.addHandler(StreamHandler())


def get_local_version(file_location):
    try:
        with open(file_location, "r") as file:
            json_data = file.read()

            parsed_json = ujson.loads(json_data)
            if parsed_json and parsed_json["version"]:
                logger_version_manager.debug("Local Version: " + str(parsed_json["version"]))
                return parsed_json["version"]
            return None

    except OSError as e:
        print("Error reading JSON file:", e)
        return None


def get_version(esp_process, url, port, version_file, files_list):
    matches = [match for match in files_list if version_file in match]
    if len(matches) > 0:
        (header, body, status_code) = esp_process.get_url_response(
            url + version_file, port
        )
        if body == None or not body["version"]:
            logger_version_manager.info("No remote version body found")
            return False

        logger_version_manager.info("Remote Version: " + str(body["version"]))
        local_version = get_local_version(version_file)
        if local_version is not None and body["version"] > local_version:
            return True

    return False

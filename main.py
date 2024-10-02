from datetime import datetime
import logging
import os
import glob
import time
import json
from pythonosc.udp_client import SimpleUDPClient


log_directory = "./logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_filename = os.path.join(
    log_directory, f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler(log_filename),  # Logs to file
        logging.StreamHandler(),  # Logs to console
    ],
)


def cleanup_old_logs(directory, keep=3):
    log_files = [f for f in os.listdir(directory) if f.endswith(".txt")]
    log_files.sort(reverse=True)  # Sort by name (newest first)

    # Remove old log files if more than 'keep' exist
    for log_file in log_files[keep:]:
        os.remove(os.path.join(directory, log_file))


def find_latest_vrc_log(directory):
    log_files = glob.glob(os.path.join(directory, "*.txt"))
    if not log_files:
        logging.info("No log files found.")
        return None

    latest_log = max(log_files, key=os.path.getmtime)
    logging.info(
        f"Current VRChat Log: {latest_log}\nRunning! ToN data should appear below~\n==================================="
    )
    return latest_log


def send_message(terrors):
    osc_client.send_message("/chatbox/input", [terrors, True, False])


def monitor_round_types(log_file):
    last_position = 0
    round_type = ""
    round_active = False
    first_run = False
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(dir_path + "/index.json") as json_file:
        data = json.load(json_file)
        terrors = data["Terrors"]
        alternates = data["Alternates"]
        while True:
            with open(log_file, "r", encoding="utf-8") as file:
                file.seek(last_position)
                lines = file.readlines()
                new_position = file.tell()

                for line in lines:
                    if not first_run:
                        if "Round was valid." in line:
                            round_active = False

                        elif round_active and (
                            ("Died in round." in line) or ("You died." in line)
                        ):
                            logging.info("Died")
                            logging.info("===================================")

                        elif round_active and ("WE WON" in line):
                            logging.info("Survived")
                            logging.info("===================================")

                        elif round_active and ("Player respawned, opted out!" in line):
                            logging.info("Respawned")
                            logging.info("===================================")

                        elif "Killers have been set" in line:
                            round_active = True
                            parts = line.split("Killers have been set")
                            if len(parts) > 1:
                                round_type = parts[1].strip().split()[-1]
                                terror1 = parts[1].strip().split()[1]
                                terror2 = parts[1].strip().split()[2]
                                terror3 = parts[1].strip().split()[3]
                                round_terrors = ""
                                match round_type:
                                    case "Alternate":
                                        round_terrors = alternates[terror1]
                                    case "Bloodbath":
                                        round_terrors = f"{terrors[terror1]}, {terrors[terror2]}, {terrors[terror3]}"
                                    case "Midnight":
                                        round_terrors = f"{terrors[terror1]}, {terrors[terror2]}, {alternates[terror3]}"
                                    case "8 Pages":
                                        round_terrors = "???"
                                    case _:
                                        round_terrors = terrors[terror1]
                                if round_type in valid_rounds:
                                    send_message(round_terrors)
                                logging.info(
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                )
                                logging.info(f"Round type: {round_type}")
                                logging.info(f"Terrors: {round_terrors}")

                last_position = new_position

            first_run = False
            time.sleep(3)


if __name__ == "__main__":
    # OSC setup
    ip = "127.0.0.1"
    port = 9000
    osc_client = SimpleUDPClient(ip, port)

    valid_rounds = {"Fog", "Bloodbath", "Midnight"}  # investigate 8pages

    # find vrc logs
    user_dir = os.getlogin()
    vrc_log_directory = f"C:\\Users\\{user_dir}\\AppData\\LocalLow\\VRChat\\VRChat"
    latest_log_file = find_latest_vrc_log(vrc_log_directory)

    cleanup_old_logs(log_directory)

    if latest_log_file:
        monitor_round_types(latest_log_file)

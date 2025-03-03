import yaml
import csv
from tws_client import TWSClient


# Load configuration from YAML file
def load_config(filename="config.yaml"):
    with open(filename, "r") as file:
        return yaml.safe_load(file)


def save_to_csv(positions, filename):
    """Saves positions to a CSV file."""
    if not positions:
        print("No positions to save.")
        return

    keys = positions[0].keys()

    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(positions)

    print(f"Positions saved to {filename}")


def main():
    config = load_config()

    # Read values from config file
    tws_config = config["tws"]
    output_file = config["output"]["file"]

    client = TWSClient(
        host=tws_config["host"],
        port=tws_config["port"],
        client_id=tws_config["client_id"],
    )

    try:
        client.connect()
        positions = client.get_positions()

        if positions:
            print("\nCurrent Positions:")
            for pos in positions:
                print(
                    f"Symbol: {pos['symbol']}, Quantity: {pos['quantity']}, Avg Price: {pos['avg_price']}"
                )

            # Save to CSV
            save_to_csv(positions, output_file)

        else:
            print("\nNo open positions.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()

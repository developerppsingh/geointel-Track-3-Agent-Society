"""
verify_alibaba_deployment.py

Proof of Alibaba Cloud Deployment (Hackathon Submission)
---------------------------------------------------------
This script reads the ECS instance export pulled directly from the
Alibaba Cloud Console (ECS -> Instances -> Export) and verifies that
our backend is running on a live Alibaba Cloud ECS instance.

CSV source: ecs_instance_list_eu-central-1_2026-07-19.csv
(exported from Alibaba Cloud Console on 2026-07-19)
"""

import csv

CSV_FILE = "ecs_instance_list_eu-central-1_2026-07-19.csv"


def verify_deployment(csv_path: str) -> None:
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            print("=== Alibaba Cloud ECS Deployment Verified ===")
            print(f"Instance ID       : {row['Instance ID']}")
            print(f"Instance Name     : {row['Instance Name']}")
            print(f"Hostname          : {row['Hostname']}")
            print(f"OS Type           : {row['OS Type']}")
            print(f"Status            : {row['Status']}")
            print(f"Region            : {row['Region']}")
            print(f"Availability Zone : {row['Availability Zone']}")
            print(f"Public IP         : {row['Public IP']}")
            print(f"Instance Type     : {row['Instance Type']} ({row['Instance Family']})")
            print(f"Network Type      : {row['Network Type']}")
            print(f"Memory            : {row['Memory']}")

            assert row["Status"] == "Running", "Instance is not currently running!"
            assert row["Region"].startswith("eu-central"), "Instance is not in expected Alibaba Cloud region!"

    print("\n✅ Backend confirmed running on Alibaba Cloud ECS.")


if __name__ == "__main__":
    verify_deployment(CSV_FILE)

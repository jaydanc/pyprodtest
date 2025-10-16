import json

def generate_report(test_data):
    with open("pyprodtest_report.json", "w") as f:
        json.dump(test_data, f, indent=2)

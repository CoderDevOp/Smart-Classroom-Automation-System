from database import ClassroomDatabase


print()
print("================================")
print("DATABASE TEST")
print("================================")
print()


database = ClassroomDatabase(
    "data/classroom.db"
)


print("Database created successfully.")


# ----------------------------------------
# OCCUPANCY TEST
# ----------------------------------------

database.log_occupancy(
    zone_name="Zone 1",
    people_count=2
)

database.log_occupancy(
    zone_name="Zone 2",
    people_count=0
)


# ----------------------------------------
# APPLIANCE EVENT TEST
# ----------------------------------------

database.log_appliance_event(
    zone_name="Zone 1",
    appliance="light",
    previous_state=False,
    current_state=True
)

database.log_appliance_event(
    zone_name="Zone 1",
    appliance="fan",
    previous_state=False,
    current_state=True
)


# ----------------------------------------
# ENERGY SESSION TEST
# ----------------------------------------

database.log_energy(
    zone_name="Zone 1",
    appliance="light",
    people_count=2,
    duration_seconds=60,
    power_watts=40
)

database.log_energy(
    zone_name="Zone 1",
    appliance="fan",
    people_count=2,
    duration_seconds=60,
    power_watts=75
)


# ----------------------------------------
# DISPLAY OCCUPANCY
# ----------------------------------------

print()
print("Recent Occupancy:")
print("--------------------------------")

for row in database.get_recent_occupancy():

    print(row)


# ----------------------------------------
# DISPLAY APPLIANCE EVENTS
# ----------------------------------------

print()
print("Recent Appliance Events:")
print("--------------------------------")

for row in database.get_appliance_events():

    print(row)


# ----------------------------------------
# DISPLAY ENERGY LOGS
# ----------------------------------------

print()
print("Recent Energy Logs:")
print("--------------------------------")

for row in database.get_energy_logs():

    print(row)


print()
print("================================")
print("DATABASE TEST COMPLETE")
print("================================")
print()
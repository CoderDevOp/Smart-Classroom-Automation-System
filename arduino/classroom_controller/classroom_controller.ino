const int MAX_ZONES = 8;

// Light pins for each possible zone
const int LIGHT_PINS[MAX_ZONES] = {
    8, 10, 12, 22, 24, 26, 28, 30
};

// Fan pins for each possible zone
const int FAN_PINS[MAX_ZONES] = {
    9, 11, 13, 23, 25, 27, 29, 31
};


String command;


void setup() {

    Serial.begin(9600);

    // Initialize all possible zone pins
    for (int i = 0; i < MAX_ZONES; i++) {

        pinMode(LIGHT_PINS[i], OUTPUT);
        pinMode(FAN_PINS[i], OUTPUT);

        digitalWrite(LIGHT_PINS[i], LOW);
        digitalWrite(FAN_PINS[i], LOW);
    }

    Serial.println("Smart Classroom Arduino Ready");
}


void loop() {

    if (Serial.available() > 0) {

        command = Serial.readStringUntil('\n');

        command.trim();

        processCommand(command);
    }
}


void processCommand(String command) {

    // Expected format:
    // Z1L1F1

    if (command.length() < 6) {

        Serial.println("Invalid command");

        return;
    }


    if (command.charAt(0) != 'Z') {

        Serial.println("Invalid zone format");

        return;
    }


    int zone = command.charAt(1) - '0';

    char lightState = command.charAt(3);

    char fanState = command.charAt(5);


    if (zone < 1 || zone > MAX_ZONES) {

        Serial.println("Invalid zone");

        return;
    }


    int index = zone - 1;


    // -----------------------------
    // LIGHT
    // -----------------------------

    if (lightState == '1') {

        digitalWrite(
            LIGHT_PINS[index],
            HIGH
        );

    }
    else if (lightState == '0') {

        digitalWrite(
            LIGHT_PINS[index],
            LOW
        );
    }


    // -----------------------------
    // FAN
    // -----------------------------

    if (fanState == '1') {

        digitalWrite(
            FAN_PINS[index],
            HIGH
        );

    }
    else if (fanState == '0') {

        digitalWrite(
            FAN_PINS[index],
            LOW
        );
    }


    Serial.print("Zone ");
    Serial.print(zone);
    Serial.println(" updated");
}
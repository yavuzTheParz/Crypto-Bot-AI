#include <iostream>
#include <string>
#include <fstream>
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>
#include <chrono>
#include <thread>

using namespace std;
using json = nlohmann::json;

// Helper: Get current time in milliseconds
long long current_time_millis() {
    return chrono::duration_cast<chrono::milliseconds>(
        chrono::system_clock::now().time_since_epoch()
    ).count();
}

int main() {
    const string symbol = "BTCUSDT";
    const string interval = "1m";
    const int limit = 1000;
    const long long interval_ms = 60 * 1000; // 1 minute

    // Set start time to, say, 7 days ago
    long long startTime = current_time_millis() - (7LL * 24 * 60 * 60 * 1000);
    long long endTime = current_time_millis();

    ofstream file("btc_data_1week.csv");
    file << "Timestamp,Open,High,Low,Close,Volume\n";

    while (startTime < endTime) {
        string url = "https://api.binance.com/api/v3/klines?symbol=" + symbol +
                     "&interval=" + interval +
                     "&limit=" + to_string(limit) +
                     "&startTime=" + to_string(startTime);

        cpr::Response response = cpr::Get(cpr::Url{url});

        if (response.status_code != 200) {
            cerr << "Request failed with code: " << response.status_code << endl;
            break;
        }

        json j = json::parse(response.text);

        if (j.empty()) {
            cout << "No more data found.\n";
            break;
        }

        for (auto& candle : j) {
            file << candle[0] << "," << candle[1] << "," << candle[2] << ","
                 << candle[3] << "," << candle[4] << "," << candle[5] << "\n";
        }

        // Update startTime to the next candle
        startTime = j.back()[0].get<long long>() + interval_ms;

        // To avoid hitting rate limits
        this_thread::sleep_for(chrono::milliseconds(500));
    }

    file.close();
    cout << "Data written to btc_data.csv\n";
    return 0;
}


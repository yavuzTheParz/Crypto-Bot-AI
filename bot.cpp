#include <iostream>
#include <binapi/api.hpp>
#include <boost/asio/io_context.hpp>
#include <chrono>
#include <ctime>
#include <binapi/websocket.hpp>
#include <binapi/pairslist.hpp>
#include <binapi/reports.hpp>
#include <binapi/flatjson.hpp>
#include <boost/asio/io_context.hpp>
#include <boost/asio/steady_timer.hpp>
#include <fstream>
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>

using namespace std;

class TradeLord
{
    string symbol = "BTCUSDT";
    string last_trade;
    float cash_at_risk;
    int trade_interval;
    float cash;
    float quantity;
    float last_price;
    string pk;
    string sk;
    boost::asio::io_context& ioctx;  // Store reference to io_context
    binapi::rest::api api;

public:
    TradeLord(boost::asio::io_context& ctx, const std::string& publicKey, const std::string& secretKey);

    string getPK();
    string getSK();
    binapi::rest::api& getAPI();  // Return by reference
    boost::asio::io_context& getIoctx();
};

TradeLord::TradeLord(boost::asio::io_context& ctx, const std::string& publicKey, const std::string& secretKey)
    : ioctx(ctx), pk(publicKey), sk(secretKey),
      api(ctx, "api.binance.com", "443", publicKey, secretKey, 10000) {}

binapi::rest::api& TradeLord::getAPI()
{
    return api;
}

string TradeLord::getPK()
{
    return pk;
}

string TradeLord::getSK()
{
    return sk;
}

boost::asio::io_context& TradeLord::getIoctx()
{
    return ioctx;
}

int main()
{
    boost::asio::io_context ioctx;

    const std::string pk = "gN9ATvZT4JivfsIpDK6bifR0aVDzZGXnbyBQed92wqmSlYbSCsFTF3eW7K5kvmwG";
    const std::string sk = "FqB27GDn5aioaErhNKauBlBi8r4dKPpnOJgCbxGv4jodiMvvvwVO3Yr04iP3Y55z";

    TradeLord tradeLord(ioctx, pk, sk);

    /*tradeLord.getAPI().account_info([](const char *fl, int ec, std::string errmsg, binapi::rest::account_info_t res) {
        if (ec)
        {
            std::cerr << "account info error: fl=" << fl << ", ec=" << ec << ", emsg=" << errmsg << std::endl;
            return false;
        }

        std::cout << "account info: " << res << std::endl;

        return true;
    });*/


    // Define parameters
    cpr::Parameters params = {
        {"symbol", "BTCUSDT"},  // Symbol: Bitcoin to USDT
        {"windowSize", "1h"}    // Rolling window: 1 hour
    };

    // Make the request
    std::string base_url = "https://api.binance.com/api/v3/ticker";  // Define the correct URL
    cpr::Response r = cpr::Get(cpr::Url{base_url}, params);

    // Check if request was successful
    if (r.status_code == 200) {
        // Parse JSON response
        nlohmann::json data = nlohmann::json::parse(r.text);
        std::cout << "Symbol: " << data["symbol"] << "\n";
        std::cout << "Price Change: " << data["priceChange"] << "\n";
        std::cout << "Price Change %: " << data["priceChangePercent"] << "%\n";
        std::cout << "Last Price: " << data["lastPrice"] << "\n";
        std::cout << "Open Price: " << data["openPrice"] << "\n";
        std::cout << "High Price: " << data["highPrice"] << "\n";
        std::cout << "Low Price: " << data["lowPrice"] << "\n";
    } else {
        std::cerr << "Error: " << r.status_code << " - " << r.error.message << std::endl;
    }

    ioctx.run();

    return EXIT_SUCCESS;
}



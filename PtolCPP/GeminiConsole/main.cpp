
//***** ** ***

#define CPR_LIBCURL_NO_CURL_EASY_HACKS // ADD THIS LINE

// Then your includes:
#include <cstdlib> // Required for getenv
#include <iostream>
#include <string>

#include <vector> // Likely needed for message history
#include <stdexcept>

//For Threading later TODO
#include <thread> // For threading (not fully used in this synchronous example)
#include <mutex>  // For thread safety if threading (not fully used)
#include <condition_variable> //If you plan threading for chat

// This is the CRUCIAL part for the 'OK' macro conflict.
// Undefine the 'OK' macro if it's already defined by some system header.
// This must come *before* any cpr headers are included.
#ifdef OK
#undef OK
#endif

// Now include cpr and json
#include "externals/cpr/include/cpr/cpr.h" // For HTTP requests...Adjust path if needed
#include "externals/json/single_include/nlohmann/json.hpp" // For JSON parsing...Adjust path if needed

// Ncurses includes
#include <ncursesw/ncurses.h> // Or <ncurses.h> if that works for you
#include <locale.h>

// Global variables for Ncurses windows (if you're using them globally)
// It's good practice to declare them at a scope where they are accessible
// by functions that need them.
WINDOW *chat_window;
WINDOW *input_window;
WINDOW *border_window;

// --- Global Mutex for UI Updates (important if multithreading API calls) ---
std::mutex ui_mutex;

// --- Configuration ---
// Your Gemini API Key - This is the key you provided.
// IMPORTANT: For production, do NOT hardcode API keys directly in source.
// Use environment variables or a secure config file.
// const std::string GEMINI_API_KEY = "AIzaSyB6yfXQ5BuiAfg8KAt1A0RrrG2sx9GUqcQ";

// Function prototypes
void setup_windows();
void cleanup_ncurses();
void print_message(WINDOW* win, const std::string& sender, const std::string& message, int color_pair);
// Add other function prototypes as needed

std::string getGeminiApiKey() {
    const char* api_key_cstr = std::getenv("GEMINI_API_KEY");

    if (api_key_cstr == nullptr) {
        // The environment variable was not found.
        // You should handle this error appropriately.
        // For development, you might print a message and exit,
        // or prompt the user, or throw an exception.
        std::cerr << "Error: GEMINI_API_KEY environment variable not set." << std::endl;
        // Example: Throw Exception then Exit the program
        throw std::runtime_error("GEMINI_API_KEY environment variable not set.");
        exit(EXIT_FAILURE);
    }

    // Convert the C-style string to a C++ std::string
    return std::string(api_key_cstr);
}

std::string gemini_api_key = getGeminiApiKey();

const std::string GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=";

// --- Function to interact with Gemini API ---
std::string callGeminiAPI(const std::string& prompt) {
    if (gemini_api_key == "YOUR_GEMINI_API_KEY" || gemini_api_key.empty()) {
        return "Error: GEMINI_API_KEY not set or invalid.";
    }

    nlohmann::json request_body = {
        {"contents", {
            {{"parts", {
                {{"text", prompt}}
            }}}
        }}
    };

    std::string full_url = GEMINI_API_URL + gemini_api_key;

//    cpr::Response r = cpr::Post(cpr::Url{GEMINI_API_ENDPOINT}, cpr::Body{json_payload.dump()}, headers);

    cpr::Response r = cpr::Post(cpr::Url{full_url},
                                 cpr::Header{{"Content-Type", "application/json"}},
                                 cpr::Body{request_body.dump()});

    if (r.status_code == 200) {
        try {
            auto json_response = nlohmann::json::parse(r.text);
            if (json_response.contains("candidates") && !json_response["candidates"].empty()) {
                if (json_response["candidates"][0].contains("content") &&
                    json_response["candidates"][0]["content"].contains("parts") &&
                    !json_response["candidates"][0]["content"]["parts"].empty() &&
                    json_response["candidates"][0]["content"]["parts"][0].contains("text")) {
                    return json_response["candidates"][0]["content"]["parts"][0]["text"].get<std::string>();
                }
            }
            return "Error: Unexpected JSON response format.";
        } catch (const nlohmann::json::parse_error& e) {
            return "Error parsing JSON response: " + std::string(e.what());
        }
    } else {
        return "Error: HTTP Status Code " + std::to_string(r.status_code) + "\nResponse Body: " + r.text;
    }
}

// --- Helper function to wrap text for the chat window ---
std::vector<std::string> wrapText(const std::string& text, int width) {
    std::vector<std::string> lines;
    std::string current_line;
    std::string::size_type start = 0;

    while (start < text.length()) {
        std::string::size_type end = text.find(' ', start);
        if (end == std::string::npos) { // No more spaces, take rest of the text
            current_line += text.substr(start);
            start = text.length();
        } else {
            std::string word = text.substr(start, end - start);
            if (current_line.length() + word.length() + 1 > width) { // +1 for space
                if (!current_line.empty()) {
                    lines.push_back(current_line);
                }
                current_line = word;
            } else {
                if (!current_line.empty()) {
                    current_line += " ";
                }
                current_line += word;
            }
            start = end + 1;
        }

        // Handle cases where a single word is longer than the width
        if (current_line.length() > width) {
            lines.push_back(current_line.substr(0, width));
            current_line = current_line.substr(width);
        }
    }
    if (!current_line.empty()) {
        lines.push_back(current_line);
    }
    return lines;
}


// --- UI Functions ---
void init_ncurses() {
    initscr();            // Start curses mode
    cbreak();             // Line buffering disabled, pass everything to program
    noecho();             // Don't echo input characters
    keypad(stdscr, TRUE); // Enable function keys (like arrow keys)
    curs_set(1);          // Show the cursor
    set_escdelay(0);      // Reduce delay for escape sequences

    if (has_colors()) {
        start_color();
        init_pair(1, COLOR_CYAN, COLOR_BLACK);   // User text
        init_pair(2, COLOR_GREEN, COLOR_BLACK);  // Gemini text
        init_pair(3, COLOR_MAGENTA, COLOR_BLACK); // System messages/borders
    }
}

// Function to set up Ncurses windows
void setup_windows() {
    int max_y, max_x;
    char c;
    getmaxyx(stdscr, max_y, max_x); // Get overall screen dimensions

    // Create a border window (optional, but good for visual separation)
    border_window = newwin(max_y, max_x, 0, 0);
    box(border_window, 0, 0); // Draw a default border
    wrefresh(border_window);

    // Chat window takes most of the screen
    chat_window = newwin(max_y - 3, max_x - 2, 1, 1); // 1 row offset, 1 col offset for border
    box(chat_window, 0, 0);
    scrollok(chat_window, TRUE); // Enable scrolling
    wrefresh(chat_window);

    // Input window at the bottom



    input_window = newwin(1, max_x - 2, max_y - 2, 1); // 1 row high, at bottom, 1 col offset
    box(input_window, 0, 0);
    wrefresh(input_window);
}

//void setup_windows() {
//    int max_y, max_x;
//    //getmaxyx(stdscr, max_y, max_x); Incorrect
//    getmaxyx(win, max_y, max_x); // Correct: getmaxyx(WINDOW*, int&, int&)
//
//    // Chat window (main display)
//    int chat_h = max_y - 5; // Height for chat history
//    int chat_w = max_x - 2; // Width for chat history
//    border_chat_window = newwin(chat_h + 2, chat_w + 2, 0, 0); // +2 for borders
//    chat_window = derwin(border_chat_window, chat_h, chat_w, 1, 1);
//    scrollok(chat_window, TRUE); // Allow scrolling
//
//    // Input window
//    int input_h = 3; // Height for input (1 line + border)
//    int input_w = max_x - 2;
//    border_input_window = newwin(input_h + 2, input_w + 2, max_y - input_h - 2, 0);
//    input_window = derwin(border_input_window, input_h, input_w, 1, 1);
//    keypad(input_window, TRUE); // Enable special keys for input window too
//
//    box(border_chat_window, 0, 0);
//    mvwprintw(border_chat_window, 0, 2, " Chat History ");
//    wattron(border_chat_window, COLOR_PAIR(3));
//    mvwprintw(border_chat_window, 0, max_x / 2 - 5, " Gemini AI ");
//    wattroff(border_chat_window, COLOR_PAIR(3));
//
//    box(border_input_window, 0, 0);
//    mvwprintw(border_input_window, 0, 2, " Enter your message (Ctrl+D to Send, Ctrl+C to Quit) ");
//    wattron(border_input_window, COLOR_PAIR(3));
//    mvwprintw(border_input_window, 0, max_x / 2 - 5, " Input ");
//    wattroff(border_input_window, COLOR_PAIR(3));
//
//    wrefresh(border_chat_window);
//    wrefresh(border_input_window);
//    wrefresh(chat_window);
//    wrefresh(input_window);
//}

// Function to print messages to the chat window
//void print_message(WINDOW* win, const std::string& sender, const std::string& message, int color_pair) {
//    if (win == nullptr) return; // Basic check
//
//    wattron(win, COLOR_PAIR(color_pair)); // Apply color for sender
//    wprintw(win, "%s: ", sender.c_str());
//    wattroff(win, COLOR_PAIR(color_pair)); // Turn off color
//
//    wprintw(win, "%s\n", message.c_str()); // Print message, newline to scroll
//    wrefresh(win); // Refresh the window to show changes
//}

void print_message(WINDOW* win, const std::string& sender, const std::string& message, int color_pair) {
    std::lock_guard<std::mutex> lock(ui_mutex); // Protect UI updates

    int max_x;
//    getmaxyx(win, stdscr, max_x); // Use stdscr for full terminal width check, or win for specific window width

    // Subtract 2 for left/right padding within the window if needed.
    // For `chat_window`, it's derived from `border_chat_window` at 1,1 so its width is already correct.
    int content_width = getmaxx(win);

    wattron(win, COLOR_PAIR(color_pair));
    wprintw(win, "\n%s: ", sender.c_str());
    wattroff(win, COLOR_PAIR(color_pair));

    std::vector<std::string> wrapped_lines = wrapText(message, content_width - (sender.length() + 2)); // Adjust for "Sender: " prefix

    bool first_line = true;
    for (const auto& line : wrapped_lines) {
        if (!first_line) {
            wprintw(win, "%s", std::string(sender.length() + 2, ' ').c_str()); // Indent subsequent lines
        }
        wprintw(win, "%s\n", line.c_str());
        first_line = false;
    }
    wrefresh(win);
    doupdate();
}

// Function to clean up Ncurses
void cleanup_ncurses() {
    delwin(chat_window);
    delwin(input_window);
    delwin(border_window); // Delete border window too
    endwin(); // End ncurses mode
}
//
//void cleanup_ncurses() {
//    delwin(chat_window);
//    delwin(input_window);
//    delwin(border_chat_window);
//    delwin(border_input_window);
//    endwin(); // End curses mode, restore terminal
//}

// --- Main Program ---
int main() {
    init_ncurses();
    setup_windows();

// Example usage of getmaxyx with stdscr
    int screen_max_y, screen_max_x;
    getmaxyx(stdscr, screen_max_y, screen_max_x);
    mvwprintw(chat_window, 0, 0, "Screen size: %d rows, %d cols", screen_max_y, screen_max_x);
    wrefresh(chat_window);

    std::string gemini_api_key = getGeminiApiKey();

    // Now you can use 'gemini_api_key' when making requests to the Gemini API
    // For example, adding it to your cpr::Header:
    cpr::Header headers = {
        {"Content-Type", "application/json"},
        {"x-goog-api-key", gemini_api_key} // This is likely how Gemini API expects it
    };

    // Test a cpr request (example)
    try {
        cpr::Response r = cpr::Get(cpr::Url{"http://httpbin.org/get"});
        if (r.status_code == 200) {
            print_message(chat_window, "\nSystem", "Successfully connected to httpbin.org!", 1);
            print_message(chat_window, "Debug", r.text.substr(0, 50) + "...", 2); // Print first 50 chars of response
        } else {
            print_message(chat_window, "Error", "Failed to connect: " + std::to_string(r.status_code), 1);
            print_message(chat_window, "Error Detail", r.error.message, 1);
        }
    } catch (const std::exception& e) {
        print_message(chat_window, "Exception", "CPR Exception: " + std::string(e.what()), 1);
    }
    std::cout << "API Key Successfully Loaded (first 5 chars): " << gemini_api_key.substr(0, 5) << "..." << std::endl;
    wrefresh(chat_window);

    print_message(chat_window, "System", "\n\n***-**-*****", 3);
    print_message(chat_window, "System", "Welcome to Gemini CLI Chat!", 3);
    print_message(chat_window, "System", "Type your message below and press Ctrl+D (EOF) to send.", 3);
    print_message(chat_window, "System", "Press Ctrl+C to quit.", 3);

    std::string user_input_buffer;
    int ch;

    // Set a timeout for getch() so we can check for resize events
    halfdelay(1); // Wait for 1/10th of a second for input

    while (true) {
        // Handle window resizing
        int new_max_y, new_max_x;
        getmaxyx(stdscr, new_max_y, new_max_x);
        if (new_max_y != LINES || new_max_x != COLS) {
            // Resize detected, redraw everything
            std::lock_guard<std::mutex> lock(ui_mutex);
            clear();
            refresh();
            setup_windows(); // Re-create and redraw windows
            // You might want to re-print chat history here, or simply assume it scrolls correctly
        }

        ch = wgetch(input_window); // Get character from input window

        if (ch == ERR) { // No input received within halfdelay timeout
            continue;
        }

        if (ch == '\n' || ch == KEY_SEND || ch == 4) { // Enter or Ctrl+D (EOF)
            if (user_input_buffer.empty()) {
                // If enter is pressed on an empty line, do nothing or show a small error
                print_message(chat_window, "System", "Please type something before sending.", 3);
                wrefresh(input_window);
                doupdate();
                continue;
            }

            print_message(chat_window, "You", user_input_buffer, 1);
            werase(input_window); // Clear input window
            wmove(input_window, 0, 0); // Move cursor to start of input
            wrefresh(input_window);
            doupdate();

            print_message(chat_window, "Gemini", "Thinking...", 2);

            // Call Gemini API (synchronous for now, blocks UI)
            std::string gemini_response = callGeminiAPI(user_input_buffer);

            // Remove "Thinking..." and print actual response
            // This is a bit tricky with scrollok(). Simpler to just add the new response.
            // For a "replace thinking" effect, you'd need to manage lines more precisely or use overlay windows.
            print_message(chat_window, "Gemini", gemini_response, 2);

            user_input_buffer.clear(); // Clear buffer for next input

            wmove(input_window, 0, 0); // Move cursor back to input start
            wrefresh(input_window);
            doupdate();

        } else if (ch == KEY_BACKSPACE || ch == 127) { // Backspace or Delete
            if (!user_input_buffer.empty()) {
                user_input_buffer.pop_back();
                int cur_y, cur_x;
                getyx(input_window, cur_y, cur_x);
                mvwdelch(input_window, cur_y, cur_x - 1); // Delete char visually
                wrefresh(input_window);
                doupdate();
            }
        } else if (ch == 3) { // Ctrl+C (ASCII for EOT)
            break; // Exit loop
        }
        else if (ch >= 32 && ch <= 126) { // Printable ASCII characters
            user_input_buffer += static_cast<char>(ch);
            waddch(input_window, ch);
            wrefresh(input_window);
            doupdate();
        }
        // For other keys (e.g., arrow keys if you wanted to implement history),
        // you'd add more `else if` conditions.
    }

    cleanup_ncurses();
    return 0;
}

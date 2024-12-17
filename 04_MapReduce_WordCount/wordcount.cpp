#include <iostream>
#include <fstream>
#include <sstream>
#include <map>
#include <vector>
#include <thread>
#include <mutex>
#include <algorithm>
#include <iomanip>

// g++ -std=c++17 -o wordcount wordcount.cpp -lpthread

std::mutex mutex;

// Function to split a string into words
std::vector<std::string> split(const std::string &text) {
    std::istringstream stream(text);
    std::vector<std::string> words;
    std::string word;
    while (stream >> word) {
        // Remove punctuation and convert to lowercase
        word.erase(std::remove_if(word.begin(), word.end(), ispunct), word.end());
        std::transform(word.begin(), word.end(), word.begin(), ::tolower);
        words.push_back(word);
    }
    return words;
}

// Map function to count words in a chunk of text
void mapFunction(const std::string &chunk, std::map<std::string, int> &localWordCount) {
    auto words = split(chunk);
    for (const auto &word : words) {
        localWordCount[word]++;
    }
}

void reduceFunction(const std::map<std::string, int> &localWordCount, std::map<std::string, int> &globalWordCount) {
    std::lock_guard<std::mutex> lock(mutex);
    for (auto it = localWordCount.begin(); it != localWordCount.end(); ++it) {
        globalWordCount[it->first] += it->second;
    }
}

int main() {
    // Read input text from a file
    std::ifstream inputFile("input.txt");
    if (!inputFile) {
        std::cerr << "Failed to open input file." << std::endl;
        return 1;
    }

    std::ostringstream buffer;
    buffer << inputFile.rdbuf();
    std::string text = buffer.str();

    // Split text into chunks (for simplicity, fixed chunk size)
    // size_t chunkSize = 1024; // For short
    // size_t chunkSize = 4.6 * 1024 * 1024 * 8; // For Bible 
    size_t chunkSize = 4.6 * 1024 * 1024 * 8;
    
    std::vector<std::string> chunks;
    for (size_t i = 0; i < text.size(); i += chunkSize) {
        chunks.push_back(text.substr(i, chunkSize));
    }

    // Map phase: process chunks in parallel
    std::vector<std::thread> mapThreads;
    std::vector<std::map<std::string, int>> localWordCounts(chunks.size());

    for (size_t i = 0; i < chunks.size(); ++i) {
        mapThreads.emplace_back(mapFunction, std::ref(chunks[i]), std::ref(localWordCounts[i]));
    }

    for (auto &thread : mapThreads) {
        thread.join();
    }

    // Reduce phase: combine local word counts
    std::map<std::string, int> globalWordCount;
    std::vector<std::thread> reduceThreads;

    for (size_t i = 0; i < localWordCounts.size(); ++i) {
        reduceThreads.emplace_back(reduceFunction, std::ref(localWordCounts[i]), std::ref(globalWordCount));
    }

    for (auto &thread : reduceThreads) {
        thread.join();
    }

    // Sort words by count in descending order
    std::vector<std::pair<std::string, int>> sortedWordCounts(globalWordCount.begin(), globalWordCount.end());
    std::sort(sortedWordCounts.begin(), sortedWordCounts.end(), [](const auto &a, const auto &b) {
        return b.second < a.second;
    });

    // Output the total word count
    int totalWords = 0;
    for (const auto &entry : globalWordCount) {
        totalWords += entry.second;
    }
    
    std::ofstream outputFile("result.txt");
    if (!outputFile) {
        std::cerr << "Failed to create result file." << std::endl;
        return 1;
    }

    outputFile << "Total words: " << totalWords << "\n\n";

    int count = 0;
    const int wordWidth = 18; 
    const int countWidth = 8;

    for (const auto &entry : sortedWordCounts) {
        outputFile << std::left << std::setw(wordWidth) << entry.first
                   << std::right << std::setw(countWidth) << entry.second << "\t";
        count++;
        if (count % 5 == 0) {
            outputFile << "\n";
        }
    }

    if (count % 5 != 0) {
        outputFile << "\n";
    }

    outputFile.close();

    std::cout << "Results is written to result.txt" << std::endl;
    return 0;
}
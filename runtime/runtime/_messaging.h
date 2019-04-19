#ifndef MESSAGING_H
#define MESSAGING_H

namespace messaging {
    std::string cobs_encode(std::string data);
    std::string cobs_decode(std::string data);
}

#endif

#include <stdio.h>              // perror
#include <arpa/inet.h>          // socket
#include <net/if.h>             // ifreq
#include <string.h>             // memset
#include <sys/ioctl.h>          // ioctl
#include <linux/if_packet.h>    // sockaddr_ll
#include <netinet/ether.h>      // ETH_ALEN
#include <unistd.h>             // usleep
#include <sys/time.h>           // gettimeofday

#define BUFFER_SIZE             1024
#define SIXTY_HERTZ             4800
#define BUFFER_SIZE_FULL        BUFFER_SIZE * SIXTY_HERTZ * 120  // capable of loading up to 120 seconds of SV messages

void busy_wait(suseconds_t usec) {
    struct timeval begin, end, elapsed;
    gettimeofday(&begin, 0);
    while (1) {
        gettimeofday(&end, 0);
        timersub(&end, &begin, &elapsed);
        if (elapsed.tv_usec >= usec) { break; }
    }
}

int get_socket() {
    int sockfd;
    if ((sockfd = socket(AF_PACKET, SOCK_RAW, IPPROTO_RAW)) < 0) {
        perror("socket");
        return sockfd;
    }
    return sockfd;
}

int get_index(int sockfd, char interface[IFNAMSIZ]) {
    struct ifreq index;
    memset(&index, 0, sizeof(struct ifreq));
    strncpy(index.ifr_name, interface, IFNAMSIZ-1);

    int status;
    if((status = ioctl(sockfd, SIOCGIFINDEX, &index)) < 0) {
        perror("SIOCGIFINDEX");
        return status;
    }

    return index.ifr_ifindex;
}

int send_sv(
    const unsigned short int sockfd, const unsigned short int nic_index, unsigned char svs[BUFFER_SIZE_FULL],
    const unsigned long int number_of_svs,
    const unsigned short int sv_length, const unsigned short int sv_expected_sleep_time
) {
    char buffer[BUFFER_SIZE];  // buffer should be the size of sv_length

    struct sockaddr_ll address;
    address.sll_ifindex = nic_index;
    address.sll_halen = ETH_ALEN;

    int status;
    for (int i = 0; i < number_of_svs; i++) {
        if (sv_expected_sleep_time > 0) {
            busy_wait(sv_expected_sleep_time);  // I don't know if usleep(0) impacts the code's performance
        }

        memset(buffer, 0, BUFFER_SIZE);

        // length = strlen((char *) pdu);  // strlen does not work bc of \x00 values inside the SV frame
        memcpy(&buffer, &svs[i * sv_length], sv_length);

        status = sendto(sockfd, buffer, sv_length, 0, (struct sockaddr*) &address, sizeof(struct sockaddr_ll));
        if (status < 0) {
            perror("Could not send message");
            return status;
        }
    }
    return 0;
}

int close_socket(int sockfd) {
    close(sockfd);
}

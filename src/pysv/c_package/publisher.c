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

int send_sv(int sockfd, int index, unsigned char pdu[BUFFER_SIZE], unsigned short int length) {
    char buffer[BUFFER_SIZE];
    memset(buffer, 0, BUFFER_SIZE);

    // length = strlen((char *) pdu);  // strlen does not work bc of \x00 values inside the SV frame
    memcpy(buffer, pdu, length);

    struct sockaddr_ll address;
    address.sll_ifindex = index;
    address.sll_halen = ETH_ALEN;

    return sendto(sockfd, buffer, length, 0, (struct sockaddr*) &address, sizeof(struct sockaddr_ll));
}

int send_sv_rt(int sockfd, int index, unsigned short int time2sleep, unsigned char pdu[BUFFER_SIZE], unsigned short int length) {

    if (time2sleep > 0) {
        usleep(time2sleep);  // I don't know if usleep(0) impacts the code's performance
    }

    return send_sv(sockfd, index, pdu, length);
}

void busy_wait_top_of_second() {
    struct timeval end;
    while (1) {
        gettimeofday(&end, 0);
        if (end.tv_usec < 1) { break; }
    }
}

int send_first_sv_busy_wait(int sockfd, int index, unsigned short int time2sleep, unsigned char pdu[BUFFER_SIZE], unsigned short int length) {

    busy_wait_top_of_second();

    return send_sv(sockfd, index, pdu, length);
}


int send_sv_busy_wait(int sockfd, int index, unsigned short int time2sleep, unsigned char pdu[BUFFER_SIZE], unsigned short int length) {

    if (time2sleep > 0) {
        busy_wait(time2sleep);  // I don't know if usleep(0) impacts the code's performance
    }

    return send_sv(sockfd, index, pdu, length);
}

int close_socket(int sockfd) {
    close(sockfd);
}

#include <stdio.h>              // printf
#include <arpa/inet.h>          // socket
#include <net/if.h>             // ifreq
#include <string.h>             // memset
#include <sys/ioctl.h>          // ioctl
#include <linux/if_packet.h>    // sockaddr_ll
#include <netinet/ether.h>      // ETH_ALEN

#define BUFFER_SIZE             1024

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

int send_sv(int sockfd, int index, unsigned char pdu[14]) {
    int len = 0;
    char buffer[BUFFER_SIZE];
    memset(buffer, 0, BUFFER_SIZE);

    memcpy(buffer, pdu, 14);
    len = 14;

    struct sockaddr_ll address;
    address.sll_ifindex = index;
    address.sll_halen = ETH_ALEN;

    int status;
    if ((status = sendto(sockfd, buffer, len, 0, (struct sockaddr*) &address, sizeof(struct sockaddr_ll))) < 0) {
        return status;
    }

    return 0;
}

int main(){
    int sockfd = get_socket();
    if (sockfd < 0) { return sockfd; }
    // printf("sockfd %d\n", sockfd);

    int index = get_index(sockfd, "lo");
    if (index < 0) { return index; }
    // printf("index %d\n", index);

    unsigned char pdu[14] = {
        0x01, 0x0c, 0xcd, 0x04, 0x00, 0x00, // dst
        0x00, 0xbe, 0x43, 0xcc, 0x53, 0x68, // src
        0x88, 0xba,                         // ether type
    };

    int status = send_sv(sockfd, index, pdu);
    if (status < 0) { return status; }
    // printf("status %d\n", status);

    return 0;
}

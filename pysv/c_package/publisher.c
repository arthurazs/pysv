// Code adapted from sendRawEth.c by biranchi2018
#include <sys/time.h>

#include <arpa/inet.h>
#include <linux/if_packet.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <net/if.h>
#include <netinet/ether.h>

#include <stdbool.h>

#define TIMER	        250 // microseconds

#define ETH_SV_TYPE	    0x88BA
#define GOOD_QUALITY	0x00
#define DERIVED_QUALITY	0x20

#define DEFAULT_IF	    "enp1s0"
#define BUF_SIZ		    1024

//cc -fPIC -shared -o publisher.so publisher.c

void busy_wait(suseconds_t usec) {
    struct timeval begin, end, elapsed;
    gettimeofday(&begin, 0);
    while (true) {
        gettimeofday(&end, 0);
        timersub(&end, &begin, &elapsed);
        if (elapsed.tv_usec >= usec) { break; }
    }
}

void add_us(struct timeval * cycle, int us) {
    if (cycle->tv_usec + us >= 1000000) {
        cycle->tv_sec += 1;
        cycle->tv_usec += us - 1000000;
    } else {
        cycle->tv_usec += us;
    }
}

int open_socket() {
	int sockfd;
	if ((sockfd = socket(AF_PACKET, SOCK_RAW, IPPROTO_RAW)) == -1) {
	    perror("socket");
	    return -1;
	}
	return sockfd;
}

int send_sv(int sockfd, unsigned char dst[6], unsigned char src[6], unsigned char cnt[2], int16_t pdu[64]) {
	struct ifreq if_idx;
	struct ifreq if_mac;
	int tx_len = 0;
	char sendbuf[BUF_SIZ];
	struct ether_header *eh = (struct ether_header *) sendbuf;
	struct iphdr *iph = (struct iphdr *) (sendbuf + sizeof(struct ether_header));
	struct sockaddr_ll socket_address;
	char ifName[IFNAMSIZ];

	/* Get interface name */
    strcpy(ifName, DEFAULT_IF);

	/* Open RAW socket to send on */
//	if ((sockfd = socket(AF_PACKET, SOCK_RAW, IPPROTO_RAW)) == -1) {
//	    perror("socket");
//	    return -1;
//	}

	/* Get the index of the interface to send on */
	memset(&if_idx, 0, sizeof(struct ifreq));
	strncpy(if_idx.ifr_name, ifName, IFNAMSIZ-1);
	if (ioctl(sockfd, SIOCGIFINDEX, &if_idx) < 0) {
	    perror("SIOCGIFINDEX");
	    return -2;
    }

	/* Get the MAC address of the interface to send on */
	memset(&if_mac, 0, sizeof(struct ifreq));
	strncpy(if_mac.ifr_name, ifName, IFNAMSIZ-1);
	if (ioctl(sockfd, SIOCGIFHWADDR, &if_mac) < 0) {
	    perror("SIOCGIFHWADDR");
	    return -3;
    }

    /* Construct the Ethernet header */
    memset(sendbuf, 0, BUF_SIZ);
    /* Ethernet header */
    memcpy(eh->ether_shost, src, 6);
    memcpy(eh->ether_dhost, dst, 6);
    /* Ethertype field */
    eh->ether_type = htons(ETH_SV_TYPE);

    struct timeval now, next_cycle, difference;
    gettimeofday(&now, NULL);
    gettimeofday(&next_cycle, NULL);
    add_us(&next_cycle, TIMER);


    tx_len = sizeof(struct ether_header);

    // APPID
    sendbuf[tx_len++] = 0x40;
    sendbuf[tx_len++] = 0x00;

    // Length
    sendbuf[tx_len++] = 0x00;
    sendbuf[tx_len++] = 0x66;

    // Reserved
    sendbuf[tx_len++] = 0x00;
    sendbuf[tx_len++] = 0x00;
    sendbuf[tx_len++] = 0x00;
    sendbuf[tx_len++] = 0x00;

    // savPdu
    sendbuf[tx_len++] = 0x60; // asn1 type
    sendbuf[tx_len++] = 0x5c; // asn1 len

    // noASDU
    sendbuf[tx_len++] = 0x80;
    sendbuf[tx_len++] = 0x01;
    sendbuf[tx_len++] = 0x01;

    // seqASDU
    sendbuf[tx_len++] = 0xa2; // asn1 type
    sendbuf[tx_len++] = 0x57; // asn1 len

    // ASDU
    sendbuf[tx_len++] = 0x30; // asn1 type
    sendbuf[tx_len++] = 0x55; // asn1 len

    // SVID
    sendbuf[tx_len++] = 0x80;
    sendbuf[tx_len++] = 0x04;
    sendbuf[tx_len++] = 0x34;
    sendbuf[tx_len++] = 0x30;
    sendbuf[tx_len++] = 0x30;
    sendbuf[tx_len++] = 0x30;

    // smpCnt
    sendbuf[tx_len++] = 0x82;
    sendbuf[tx_len++] = 0x02;
    memcpy(sendbuf + tx_len++, cnt, 2);
    tx_len++;

    // confRev
    sendbuf[tx_len++] = 0x83;
    sendbuf[tx_len++] = 0x04;
    sendbuf[tx_len++] = 0x00;
    sendbuf[tx_len++] = 0x00;
    sendbuf[tx_len++] = 0x00;
    sendbuf[tx_len++] = 0x01;

    // smpSynch
    sendbuf[tx_len++] = 0x85;
    sendbuf[tx_len++] = 0x01;
    sendbuf[tx_len++] = 0x02;

    // PhsMeas
    sendbuf[tx_len++] = 0x87; // asn1 type
    sendbuf[tx_len++] = 0x40; // asn1 len

    // PDU
    memcpy(sendbuf + tx_len++, pdu, 64);
    tx_len += 63;

    /* Index of the network device */
    socket_address.sll_ifindex = if_idx.ifr_ifindex;
    /* Address length*/
    socket_address.sll_halen = ETH_ALEN;
    /* Destination MAC */
    memcpy(socket_address.sll_addr, dst, 6);

    /* Send packet */
    if (sendto(sockfd, sendbuf, tx_len, 0, (struct sockaddr*)&socket_address, sizeof(struct sockaddr_ll)) < 0) {
        printf("Send failed\n");
        return -4;
    }

    gettimeofday(&now, NULL);
    timersub(&next_cycle, &now, &difference);

    if (difference.tv_sec == 0) {
        if (difference.tv_usec >0 ) {
            busy_wait(difference.tv_usec);
        }
    }

    add_us(&next_cycle, TIMER);

	return 0;
}
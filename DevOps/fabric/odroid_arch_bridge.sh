#!/bin/bash

iface=enp0s20f0u2
oface=wlp2s0

iptables -F
iptables -X

iptables -t nat -A POSTROUTING -o $iface -j MASQUERADE
iptables -A FORWARD -i $iface -o $oface -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $oface -o $iface -j ACCEPT

iptables -t nat -A POSTROUTING -o $oface -j MASQUERADE
iptables -A FORWARD -i $oface -o $iface -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $iface -o $oface -j ACCEPT

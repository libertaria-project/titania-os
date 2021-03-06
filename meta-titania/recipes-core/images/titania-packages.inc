# Titania own software
IMAGE_INSTALL += "ux-titania datafs-resizer http-splash"

IMAGE_INSTALL += "sudo zram systemd-analyze strace tcpdump"

# Network and discovery
IMAGE_INSTALL += "networkmanager avahi-daemon llmnrd"

# Docker
# TODO: remove manifest tool when upgrading to
# docker that the supports manifest command
IMAGE_INSTALL += "docker dapp manifest-tool"

# Network awareness and port forwards
IMAGE_INSTALL += "network-info forward-port"

# Add firmware, this is needed for WiFi on RaspberryPi
IMAGE_INSTALL += "linux-firmware-bcm43430"

# Apparently this adds RPi3B+ support
# Commented ones are apparently bluetooth
# Leaving them out for now
# IMAGE_INSTALL += "linux-firmware-bcm43455"
# linux-firmware-bcm43430a1-hcd linux-firmware-bcm4345c0-hcd"

# From v1.1.0, the titania-ux repo has been merged into titania-os repo
# # Merge UX version with main OS-release file
# append_ux_id () {
#     cat ${IMAGE_ROOTFS}${sysconfdir}/titania-ux-version >> ${IMAGE_ROOTFS}${sysconfdir}/os-release
#     rm ${IMAGE_ROOTFS}${sysconfdir}/titania-ux-version
# }
# ROOTFS_POSTPROCESS_COMMAND += "append_ux_id ; "

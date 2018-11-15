#!/bin/sh
LICENSE = "GPL-3.0"
LIC_FILES_CHKSUM = "file://LICENSE.md;md5=f149fa3bc39a974fe62c04649f34883a"

require titania-rootfs.inc

inherit lezimg

##### Raspberry PI base image with splash and ssh
####include recipes-core/images/rpi-basic-image.bb
include recipes-core/images/core-image-minimal.bb

IMAGE_CLASSES += " lezimg"

IMAGE_FEATURES += " ssh-server-dropbear "
# TODO +splash

IMAGE_INSTALL += " \
    kernel-modules \
"

##### Cause datafs image to be built
####do_image_rpi_sdimg[depends] += "titania-datafs-image:do_build"

require titania-packages.inc
require user-setup.inc
require clean-logs.inc
require sync-clock.inc
require persistent.inc
require systemd-coma-dot.inc

# TODO: maybe separate in a dedicated include for more board support
# - issues: currently based directly on meta-raspberrypi

# Inject additional partitions:
# - Second root of size ROOTFS_SIZE
# - Data partition of DATAFS_SIZE (extended to the end of the drive on the first run)
# TODO: maybe split DATA partition to a separate state partition
# but this requires either GPT (bad for bootloader on RPi) or
# an extended partition
# TODO: label datafs?
# TOOD: can we query that somehow?
DATAFS_FILENAME ?= "titania-datafs-image-${MACHINE}.ext4"

#### IMAGE_CMD_rpi-sdimg_append() {
####     # Modifying the name of the kernel on VFAT
####     # TODO: `pyro` branch always names the kernel `uImage` whereas `master` uses an env var. Watch out for upgrades.
#### #    mdel -i ${WORKDIR}/boot.img ::${KERNEL_IMAGETYPE}
#### #    mcopy -i ${WORKDIR}/boot.img -s ${DEPLOY_DIR_IMAGE}/${KERNEL_IMAGETYPE}${KERNEL_INITRAMFS}-${MACHINE}.bin ::${KERNEL_IMAGETYPE}_a
#### 
####     # We need to rewrite the VFAT partition in order to avoid patching or copypasting meta-raspberrypi code
####     dd if=${WORKDIR}/boot.img of=${SDIMG} conv=notrunc seek=1 bs=$(expr ${IMAGE_ROOTFS_ALIGNMENT} \* 1024)
#### 
####     # Update SD card image size
####     # TODO: can we get IMAGE_SIZE from other image?
####     DATAFS_SIZE=$(du --apparent-size -Hk "${DEPLOY_DIR_IMAGE}/${DATAFS_FILENAME}" | cut -f1)
####     echo "Creating data file system ${DATAFS_SIZE} KiB"
####     NEW_SDIMG_SIZE=$(expr ${SDIMG_SIZE} + ${ROOTFS_SIZE} + ${DATAFS_SIZE})
####     dd if=/dev/zero of=${SDIMG} bs=1024 count=0 seek=${NEW_SDIMG_SIZE}
#### 
####     # Start locations of second root and data
####     # TODO: check alignment
####     ROOT_B_START=${SDIMG_SIZE}
####     ROOT_B_END=$(expr ${ROOTFS_SIZE} + ${SDIMG_SIZE})
####     DATAFS_START=${ROOT_B_END}
####     DATAFS_END="-1s"
#### 
####     # Create additional partitions
####     parted -s ${SDIMG} -- unit KiB mkpart primary ext2 ${ROOT_B_START} ${ROOT_B_END}
####     parted -s ${SDIMG} -- unit KiB mkpart primary ext2 ${DATAFS_START} ${DATAFS_END}
#### 
####     # We currently leave RootB empty to preserve space of the image
####     # This is where the flasher would be putting the update anyway
#### 
####     # Burning datafs
####     # Using large `bs` for offsets results in serious memory requirements
####     dd if=${DEPLOY_DIR_IMAGE}/${DATAFS_FILENAME} of=${SDIMG} conv=notrunc seek=${DATAFS_START} bs=1024
#### 
####     parted ${SDIMG} print
#### }

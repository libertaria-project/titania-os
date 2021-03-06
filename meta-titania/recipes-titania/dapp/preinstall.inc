PACKAGES += " dapp-preinstall"

# Backport of the contrib file from modern Docker (Moby) codebase
# TODO: send a patch upstream
# TODO: upgrade docker eventually and use the file from Docker package?
SRC_URI += "file://download-frozen-image-v2.sh"

# Preinstalled images for datafs
# The runners are in docker-dapp package because this one isn't pulled in by the main image

DOCKER_PREINSTALL_DIR ?= "/titania/docker/preinstall"
DAPP_LOCAL_DIR ?= "/dapp"
FILES_${PN}-preinstall = "${DOCKER_PREINSTALL_DIR}/* ${DAPP_LOCAL_DIR}/*"

# We need those on the host for the download-frozen-image.sh script
DEPENDS += "curl-native jq-native ca-certificates-native go-native"

# Note that although the download is not part of do_fetch routine the script is smart
# enough not to download the files which are already there and have a valid checksum
# This acts as a do_install cache
# This cache is susceptible to -c clean instead of -c cleanall as you would expect for Yocto
# WARNING: use -f -c install if you want to force rebuild
do_install_append() {
    # curl-native has a built-in location for certificates
    # inform it where to take sysroot certificates from
    export CURL_CA_BUNDLE="${STAGING_ETCDIR_NATIVE}/ssl/certs/ca-certificates.crt"

    for image in ${DOCKER_IMAGE_PREINSTALL}; do
        # TODO: Can we make it a part of do_fetch and save to downloads?
        IMAGE_SAFE_FILENAME=$(echo $image | grep -o '^[^@:]*' | tr '/' '_')
        IMAGE_DIR="${WORKDIR}/images/$IMAGE_SAFE_FILENAME"
        echo "Saving $image to $IMAGE_DIR."

        # TODO: when we've patched upstream use this location:  ${S}/contrib/
        # and remove the copy from our repo

        if [ ${HOST_ARCH} = "x86_64" ]; then
            DOCKER_ARCH="amd64"
        else
            DOCKER_ARCH="arm"
        fi

        ARCH=$DOCKER_ARCH ${WORKDIR}/download-frozen-image-v2.sh $IMAGE_DIR $image
        install -d ${D}${DOCKER_PREINSTALL_DIR}

        # Pinpoint locations, make sure we don't pull old stuff from the directories in
        # Black magic explained: 
        #   - take .[0].Config from manifest.json
        #   - take .[0].Layers from manifest.json, substring 64 characters, unwrap
        #   - combine both
        #   - unwrap
        BLACK_MAGIC='[.[0].Config,(.[0].Layers | map(.[0:64]) | .[] )] | .[]'
        HASHFILES=$(jq --raw-output "$BLACK_MAGIC" < $IMAGE_DIR/manifest.json)

        # Not using compression to speed the boot up
        # Whole SD card image is compressed afterwards
        tar -cC $IMAGE_DIR \
            -f ${D}${DOCKER_PREINSTALL_DIR}/${IMAGE_SAFE_FILENAME}.tar \
            $HASHFILES manifest.json repositories

        # Creating a digest file as well
        # NOTE: assuming we have a digest!
        echo $image | grep -o 'sha256:.*$' > ${D}${DOCKER_PREINSTALL_DIR}/${IMAGE_SAFE_FILENAME}.digest
    done
}

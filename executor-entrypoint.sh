#!/bin/sh
set -eu

# Gradle's base image declares this path as an ephemeral Docker volume. It is
# executable even where Docker Desktop enforces noexec on tmpfs. Seed it from
# the immutable image cache; no dependency can be downloaded at runtime.
# Root is read-only at runtime. The pre-warmed cache lives in the image and is
# copied to tmpfs for this invocation so Gradle cannot persist state or fetch.
export GRADLE_USER_HOME=/tmp/gradle
export HOME=/tmp/home
export ANDROID_USER_HOME=/tmp/android
mkdir -p "$HOME" "$GRADLE_USER_HOME" "$ANDROID_USER_HOME"
cp -a /opt/gradle-cache/. "$GRADLE_USER_HOME/"
export ANDROID_HOME=/opt/android-sdk
export ANDROID_SDK_ROOT=/opt/android-sdk
export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"
exec "$@"

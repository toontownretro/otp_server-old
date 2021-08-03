//
// Package.pp
//
// This file defines certain configuration variables that are to be
// written into the various make scripts.  It is processed by ppremake
// (along with the Sources.pp files in each of the various
// directories) to generate build scripts appropriate to each
// environment.
//
// This is the package-specific file, which should be at the top of
// every source hierarchy.  It generally gets the ball rolling, and is
// responsible for explicitly including all of the relevent Config.pp
// files.



// What is the name and version of this source tree?
#if $[eq $[PACKAGE],]
  #define PACKAGE otp_server
  #define VERSION 0.80
#endif


// Where should we find the TOONTOWN source directory?
#if $[TOONTOWN_SOURCE]
  #define TOONTOWN_SOURCE $[unixfilename $[TOONTOWN_SOURCE]]
#elif $[or $[CTPROJS],$[TOONTOWN]]
  // If we are presently attached, use the environment variable.
  #define TOONTOWN_SOURCE $[unixfilename $[TOONTOWN]]
  #if $[eq $[TOONTOWN],]
    #error You seem to be attached to some trees, but not TOONTOWN!
  #endif
#else
  // Otherwise, if we are not attached, we guess that the source is a
  // sibling directory to this source root.
  #define TOONTOWN_SOURCE $[standardize $[TOPDIR]/../toontown]
#endif

// Where should we install OTP_SERVER?
#if $[OTP_SERVER_INSTALL]
  #define OTP_SERVER_INSTALL $[unixfilename $[OTP_SERVER_INSTALL]]
#elif $[CTPROJS]
  #set OTP_SERVER $[unixfilename $[OTP_SERVER]]
  #define OTP_SERVER_INSTALL $[OTP_SERVER]/built
  #if $[eq $[OTP_SERVER],]
    #error You seem to be attached to some trees, but not OTP_SERVER!
  #endif
#else
  #defer OTP_SERVER_INSTALL $[unixfilename $[INSTALL_DIR]]
#endif


// Also get the TOONTOWN Package file and everything that includes.
#if $[not $[isfile $[TOONTOWN_SOURCE]/Package.pp]]
  #printvar TOONTOWN_SOURCE
  #error TOONTOWN source directory not found from otp_server!  Are you attached properly?
#endif

#include $[TOONTOWN_SOURCE]/Package.pp

// Define the inter-tree dependencies.
#define NEEDS_TREES toontown $[NEEDS_TREES]
#define DEPENDABLE_HEADER_DIRS $[DEPENDABLE_HEADER_DIRS] $[TOONTOWN_INSTALL]/include

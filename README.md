# InkyPiZeroW

Forked from [InkyPi](https://github.com/fatihak/InkyPi), InkyPiZeroW is made to fix a singular issue when trying to run this on a Raspberry Pi Zero W: Screenshots not working. Why do screenshots not work? Chromium, firefox, and most other modern headless browsers no longer support the ARMv6 instruction set and require ARMv7.

How are we going to fix this?

Offload the screenshots to a separate backend server hosted on a device that is not the PiZero.

Is this a lot of work instead of just buying a newer raspberry pi? Yes.

But have you seen the availability of Raspberry Pi's these days? Yeah they are difficult to obtain.

I do not know how well I am going to build or maintain this, but I will do my best to document everything as it is done.

The important thing to note though is that

> **This is a quick and dirty way to solve a problem right now**

I will try to redo things more properly and with better documentation, but I make no guarantees of that.

## Setup

### InkyPiBackend (Backend on your own device)

#### Requirements

- [Node.js v22+](https://nodejs.org/en/download) I recommend using Node Version Manager (nvm) to make downloading easier
- [Puppeteer](https://pptr.dev/) and some [dependencies](https://pptr.dev/troubleshooting#chrome-doesnt-launch-on-linux)

#### Setup Node

Once those are downloaded, you can just run

```bash
cd InkyPiBackend
npm i
node .
```

To run the backend. By default, it runs on port 8000. If you need a different port, you can just change the index.js file

(TODO: Create config file for port)

There are numerous ways to host a node webserver. I will leave that as an exercise to the reader to complete.

### InkyPi (Frontend on PiZero)

The setup for InkyPiZeroW is pretty much the same as the base project so I will redirect you there for most of the installation and configuration process.

The _one_ important exception is within `src/utils/image_utils.py`

**Line 117 needs to be changed with the ip address or url to your backend.**

Good luck! And if you find any issues or improvements, please submit an issue. I don't know how well maintained this will be, but maybe other people would find it useful.

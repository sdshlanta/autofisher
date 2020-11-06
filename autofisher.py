# import required libraries
import argparse
import signal
from threading import Timer
from time import time

import cv2
import pyautogui
from vidgear.gears import ScreenGear

# Setup globals
holdoff_good = True
running = True

def cast():
    pyautogui.click(button='right')

def holdoff_good_callback():
    global holdoff_good
    holdoff_good = True

def signal_handler(sig, frame):
    global running
    running = False

def main():
    # Stores if we are waiting for the holdoff timer to return
    global holdoff_good
    # Stores if ctrl + c has been pressed
    global running
    # define dimensions of screen w.r.t to given monitor to be captured
    options = {
        'top': args.top,
        'left': args.left,
        'width': args.width,
        'height': args.length
    }

    # open video stream with defined parameters
    stream = ScreenGear(
        monitor=args.monitor,
        logging=True,
        **options
    ).start()

    # Setup SIGINT handler for ctrl + c in a slightly more elegant way than
    # try/except with KeyboardInterrupt
    signal.signal(signal.SIGINT, signal_handler)

    # Loop until ctrl + c is pressed
    while running:
        # read frames from stream
        frame = stream.read()

        # check for frame if Nonetype
        if frame is None:
            print('Error grabing frame data! Exiting.')
            break

        # Knock out the color from the image to make thresholding easier
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Set all pixles dimmer than args.threshold to 0
        _, frame = cv2.threshold(frame, args.threshold, 255, cv2.THRESH_BINARY)

        # If we are still inside the holdoff period we skip the frame summing
        # and checking
        if holdoff_good:
            # Sum up all pixles in the frame, when the bobber is underwater
            # the scene should be all 0s.
            frame_sum = frame.sum()

            if frame_sum == 0 :
                Timer(args.delay, holdoff_good_callback).start()
                Timer(args.recast, cast).start()
                holdoff_good = False
                pyautogui.click(button='right')

        # Show output window if we are in debug mode
        if args.debug:
            cv2.imshow("Output Frame", frame)

            # check for 'q' key if pressed
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    # close output window
    cv2.destroyAllWindows()

    # safely close video stream
    stream.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        'AutoFisher',
        description='A program for automatically realling and casting a '
                    'fishing poll in Minecraft based on screen capture.  '
                    'Be sure to turn off your HUD with F1 and with your '
                    'fishing rod already cast.'
    )
    parser.add_argument('--debug',
        help='Show the captured region of the screen after thresholding '
             'and RGB->BW color cut.  Useful for debugging undesired casts.',
        action='store_true'
    )
    parser.add_argument('-t', '--threshold',
        help='Sets the cutoff point where when below, a captured pixel '
             'will be set to 0.  Will likely need to be adjusted based on '
             'background content of scene.  Defaults to 150 out of 255',
        type=int,
        default=150,
        choices=range(0,256),
        metavar="[0-255]"
    )
    parser.add_argument('-d', '--delay',
        help='Sets the holdoff between when the program detects a bite and '
             'when it starts looking again in seconds.  Defaults to 3.0 '
             'seconds',
        type=float,
        default=3.0
    )
    parser.add_argument('-m', '--monitor',
        help='The monitor number Minecraft is running on.  Defaults to 2 '
             'because thats the one that displays it on my system.',
        type=int,
        default=2
    )
    parser.add_argument('-y', '--top',
        help='The number of pixles down from the top of the screen to start '
             'capturing from.  Defaults to 500 as that is a reasonable value '
             'for fullscreen minecraft running on a 1920x1080 monitor.',
        type=int,
        default=500
    )
    parser.add_argument('-x', '--left',
        help='The number of pixles down from the left of the screen to start '
             'capturing from.  Defaults to 900 as that is a reasonable value '
             'for fullscreen minecraft running on a 1920x1080 monitor.',
        type=int,
        default=900
    )
    parser.add_argument('-l', '--length',
        help='The number of pixles down from y to start capturing from.  '
             'Defaults to 500 as gives enough length to track the bobber even '
             'if it comes in contact with a fish on re-cast.  This value may '
             'require fiddling depending on how you are casting and your '
             'surroundings',
        type=int,
        default=500
    )
    parser.add_argument('-w', '--width',
        help='The number of pixles left of x to start capturing from.  '
             'Defaults to 100 as gives enough length to track the bobber even '
             'when it varies side to side while cutting down on noise.  This '
             'value may require fiddling depending on how you are casting and '
             'your surroundings',
        type=int,
        default=100
    )
    parser.add_argument('-r', '--recast',
        help='The delay in seconds between realing the rod in and casting it '
             'again in seconds.  Defaults to 1.0',
        type=float,
        default=1.0
    )

    args = parser.parse_args()
    main()

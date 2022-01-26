import argparse

from ams_jetcis.scripts import sensor_script_example
# from ams_jetcis.scripts import capture_images
# from ams_jetcis.scripts import process_images

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    script_arg =parser.add_argument("-f", "--script", type=str, default='sensor_script_example',
                        help="which script to run, sensor_script_example or capture_images or process_images")
    parser.add_argument("-s", "--sensor", type=str,
                        default='mira050', help="which sensor")
    parser.add_argument("-t", "--timestamp", type=str,
                        default='0000', help="which timestamp, only used in the processing script")

    args = parser.parse_args()
    script = args.script
    sensor = args.sensor

    print(f'######## SCRIPTING ENVIRONMENT STARTED ################')
    print(f'######## script: {args.script} ################')

    if script == 'capture_images':
        capture_images.run()
    elif script == 'process_images':
        process_images.run()
    elif script == 'sensor_script_example':
        sensor_script_example.run()
    else:
        raise argparse.ArgumentError(argument = script_arg , message = 'unknown argument for script type')
    # parser.add_argument("-e","--exp_time", type=int, default=1000, help="the exp time in us")
    # parser.add_argument("-g","--gain", type=int, default=1, help="the gain")

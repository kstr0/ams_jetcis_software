
def automated_measurement():
    comment = 'dark'
    test_case = 1
    device = 0
    sensor = 'mira050'
    bitmodes =  ['12bit'] #,'10bit', '10bithighspeed']
    exposures_us = np.arange(100,1000, 200)
    agains = [1] #,2,4]
    dgains = [1] #,4]
    pictures_per_shot = 10
    
    dir_results = pathlib.Path(r'./12bit_sweep_mira050_lowfpn_1_dark')
    im_dir = dir_results / sensor / str(f"testcase{test_case}")
    sensor = Mira050(imagertools=ImagerTools(printfun=None, port=0, rootPW='jetcis'))
    sensor.cold_start()
    sensor.init_sensor(bit_mode='12bit', analog_gain=1)
    sensor.temperature=int(sensor.get_temperature())
    # if not os.path.exists(im_dir):
    #     os.makedirs(im_dir)
    # if not pathlib.Path(im_dir).exists:
    pathlib.Path(im_dir).mkdir(parents=True, exist_ok=True)
    print(im_dir)
    means = []
    fpns = []
    row_fpns = []
    col_fpns = []
    noises = []
    row_noises = []
    # Execute measurements
    if not os.path.exists(dir_results/'results.csv'):
        exists = False
    else:
        exists = True
    #with open(dir_results/'results.txt', "a") as f:
    with open(dir_results/'results.csv', "a+") as f:
        writer = csv.writer(f)
        header = ['bitmode', 'again', 'dgain', 'exp_us', 'temp', 'mean', 'fpn', 'row_fpn', 'col_fpn', 't_noise', 'row_noise', 'lowfpn', 'filename','count']

        if not exists:
            writer.writerow(header)

        for low_fpn in [True]:
            sensor.low_fpn = low_fpn
            for bitmode in bitmodes:
                for again in agains:
                    for dgain in dgains:
             
                        # sensor.cold_start()
                        #sensor.check_sensor()
                        sensor.cold_start()

                        sensor.temp_cor=True

                        sensor.init_sensor(bit_mode=bitmode, analog_gain=again)
                        # set_dgain(imager, dgain,sensor)
                        time.sleep(0.1)

                        for exposure_us in exposures_us:
                            sensor.set_exposure_us(time_us=exposure_us)
                            images = []
                            time.sleep(0.4)
                            images = sensor.imager.grab_images(pictures_per_shot)
                            comment=f'lowfpn{low_fpn}'
                            fname=f'{bitmode}_again_{again}_dgain_{dgain}_exp_us_{exposure_us:4.0f}_temp_{sensor.temperature}_{comment}'
                            sensor.imager.save_images(imgs=images, dir_fname = im_dir/fname)
                            #images = sensor.imager.saveTiff(
                            #    fname=f'{bitmode}_again_{again}_dgain_{dgain}_exp_us_{exposure_us:4.0f}_temp_{temperature}_{comment}', count=pictures_per_shot, save=False)
                            mean, fpn, row_fpn, col_fpn, t_noise, row_noise = statistics(
                                images[:,60:160,290:390])
                            # imgs = sensor.imager.grab_images(imager, count=pictures_per_shot, save_im=1,
                            #                     fname=(f'./{im_dir}/{bitmode}_again_{again}_dgain_{dgain}_exp_ms_{exposure_ms:3.2f}_temp_{temperature}_{comment}'))
                            print(f'MEAN of 1 series: {np.mean(images,axis =(1,2))}')
                            means.append(mean)
                            fpns.append(fpn)
                            row_fpns.append(row_fpn)
                            col_fpns.append(col_fpn)
                            noises.append(t_noise)
                            row_noises.append(row_noise)
                            # f.write(f'### {bitmode}_again_{again}_dgain_{dgain}_exp_us_{exposure_us:4.0f}_temp_{sensor.temperature}_ ###\n')
                            # f.write("mean [DN]: {:.03f}\n".format(mean))
                            # f.write("FPN [DN]: {:.03f}\n".format(fpn))
                            # f.write("row FPN [DN]: {:.03f}\n".format(row_fpn))
                            # f.write("col FPN [DN]: {:.03f}\n".format(col_fpn))
                            # f.write("Noise [DN]: {:.03f}\n".format(t_noise))
                            # f.write("Row noise [DN]: {:.03f}\n".format(row_noise))
                            # f.write("\n".format(row_noise))
                            data = [bitmode, again, dgain, exposure_us, sensor.temperature, mean, fpn, row_fpn, col_fpn, t_noise, row_noise, low_fpn, fname, pictures_per_shot]
                            writer.writerow(data)
                        print(f'means: {means}')
                        print(f'means 12b 10b 10bhs 124')
                        
                        # plt.style.use('seaborn-whitegrid')

                        # plt.scatter(means, fpns)
                        # plt.savefig(f'fpn_{again}')
                        # plt.close()
                        # plt.scatter(means, row_fpns)
                        # plt.savefig(f'row_fpn_{again}')
                        # plt.close()
                        # plt.scatter(means, col_fpns)
                        # plt.savefig(f'col_fpn_{again}')
                        # plt.close()
                        # plt.scatter(means, noises)
                        # plt.savefig(f'noise_{again}')
                        # plt.close()

"""
Example:
    Train a CycleGAN model:
        python train.py --dataroot ./datasets/maps --name maps_cyclegan --model cycle_gan
    Train a pix2pix model:
        python train.py --dataroot ./datasets/maps --name maps_pix2pix --model pix2pix --direction BtoA
    Train a SMAPGAN model:
        python train.py --dataroot ./datasets/maps --name maps_smapgan --model smapgan
"""
import time
from options.train_options import TrainOptions
from data import create_dataset
from models import create_model
from util.visualizer import Visualizer

if __name__ == '__main__':
    opt = TrainOptions().parse()   # get training options
    
    opt.dataset_mode = 'aligned'
    datasetP = create_dataset(opt)  # create a paired dataset
    datasetP_size = len(datasetP)   # get the number of images in the dataset.
    print('The number of paired training images = %d' % datasetP_size)
    
    # opt.dataset_mode = 'unaligned'
    # datasetU = create_dataset(opt)  # create a unpaired dataset
    # datasetU_size = len(datasetU)   # get the number of images in the dataset.
    # print('The number of unpaired training images = %d' % datasetU_size)

    model = create_model(opt)      # create a model given opt.model and other options
    model.setup(opt)               # regular setup: load and print networks; create schedulers
    visualizer = Visualizer(opt)   # create a visualizer that display/save images and plots
    total_iters = 0                # the total number of training iterations

    upper_bound = float('inf')
    lower_bound = float('-inf')
    if ',' in opt.gradloss_epoch:
        lower_bound, upper_bound = map(int, opt.gradloss_epoch.split(','))

    for epoch in range(opt.epoch_count, opt.niter + opt.niter_decay + 1):    # outer loop for different epochs; we save the model by <epoch_count>, <epoch_count>+<save_latest_freq>
        epoch_start_time = time.time()  # timer for entire epoch
        iter_data_time = time.time()    # timer for data loading per iteration
        epoch_iter = 0                  # the number of training iterations in current epoch, reset to 0 every epoch

        if epoch >= lower_bound and epoch <= upper_bound:
            model.GraLoss_coef = 1.0
        else:
            model.GraLoss_coef = 0.0
        
        # # unpaired part - CycleGAN mode.
        # for i, data in enumerate(datasetU):  # inner loop within one epoch
        #     iter_start_time = time.time()  # timer for computation per iteration
        #     if total_iters % opt.print_freq == 0:
        #         t_data = iter_start_time - iter_data_time
        #     visualizer.reset()
        #     total_iters += opt.batch_size
        #     epoch_iter += opt.batch_size
        #     model.set_input(data)         # unpack data from dataset and apply preprocessing
        #     model.optimize_parameters()   # calculate loss functions, get gradients, update network weights

        #     if total_iters % opt.display_freq == 0:   # display images on visdom and save images to a HTML file
        #         save_result = total_iters % opt.update_html_freq == 0
        #         model.compute_visuals()
        #         visualizer.display_current_results(model.get_current_visuals(), epoch, save_result)

        #     if total_iters % opt.print_freq == 0:    # print training losses and save logging information to the disk
        #         losses = model.get_current_losses()
        #         t_comp = (time.time() - iter_start_time) / opt.batch_size
        #         visualizer.print_current_losses(epoch, epoch_iter, losses, t_comp, t_data)
        #         if opt.display_id > 0:
        #             visualizer.plot_current_losses(epoch, float(epoch_iter) / datasetU_size, losses)

        #     if total_iters % opt.save_latest_freq == 0:   # cache our latest model every <save_latest_freq> iterations
        #         print('saving the latest model (epoch %d, total_iters %d)' % (epoch, total_iters))
        #         save_suffix = 'iter_%d' % total_iters if opt.save_by_iter else 'latest'
        #         model.save_networks(save_suffix)

        #     iter_data_time = time.time()
            
        # paired part - pix2pix mode.
        for i, data in enumerate(datasetP):  # inner loop within one epoch
            iter_start_time = time.time()  # timer for computation per iteration
            if total_iters % opt.print_freq == 0:
                t_data = iter_start_time - iter_data_time
            visualizer.reset()
            total_iters += opt.batch_size
            epoch_iter += opt.batch_size
            model.set_input(data)         # unpack data from dataset and apply preprocessing
            model.optimize_parameters(lambda_paired_loss = 1., epoch_ratio = (1.*epoch/(opt.niter + opt.niter_decay)))   # calculate loss functions, get gradients, update network weights

            if total_iters % opt.display_freq == 0:   # display images on visdom and save images to a HTML file
                save_result = total_iters % opt.update_html_freq == 0
                model.compute_visuals()
                visualizer.display_current_results(model.get_current_visuals(), epoch, save_result)

            if total_iters % opt.print_freq == 0:    # print training losses and save logging information to the disk
                losses = model.get_current_losses()
                t_comp = (time.time() - iter_start_time) / opt.batch_size
                visualizer.print_current_losses(epoch, epoch_iter, losses, t_comp, t_data)
                if opt.display_id > 0:
                    visualizer.plot_current_losses(epoch, float(epoch_iter) / datasetP_size, losses)

            if total_iters % opt.save_latest_freq == 0:   # cache our latest model every <save_latest_freq> iterations
                print('saving the latest model (epoch %d, total_iters %d)' % (epoch, total_iters))
                save_suffix = 'iter_%d' % total_iters if opt.save_by_iter else 'latest'
                model.save_networks(save_suffix)

            iter_data_time = time.time()
        
        if epoch % opt.save_epoch_freq == 0:              # cache our model every <save_epoch_freq> epochs
            print('saving the model at the end of epoch %d, iters %d' % (epoch, total_iters))
            model.save_networks('latest')
            model.save_networks(epoch)

        print('End of epoch %d / %d \t Time Taken: %d sec' % (epoch, opt.niter + opt.niter_decay, time.time() - epoch_start_time))
        model.update_learning_rate()                     # update learning rates at the end of every epoch.

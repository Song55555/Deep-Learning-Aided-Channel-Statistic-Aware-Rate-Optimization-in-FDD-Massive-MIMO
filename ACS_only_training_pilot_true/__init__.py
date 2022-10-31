import argparse
import numpy as np
from torch.utils.data import Dataset
from scipy.linalg import toeplitz

def arg_generate():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_epochs", type=int, default=5, help="number of epochs of training")
    parser.add_argument("--batch_size", type=int, default=5, help="size of the batches")
    parser.add_argument("--batch_num_per_epoch", type=int, default=2, help="size of the batches")
    parser.add_argument("--lr", type=float, default=0.0001, help="adam: learning rate")
    parser.add_argument("--b1", type=float, default=0.9, help="adam: decay of first order momentum of gradient")
    parser.add_argument("--b2", type=float, default=0.999, help="adam: decay of first order momentum of gradient")
    parser.add_argument("--train_size", type=int, default=2, help="number of training set and validation set")
    parser.add_argument("--sample_per_file", type=int, default=5000, help="number of training set and validation set")
    parser.add_argument("--val_size", type=int, default=5, help="number of training set and validation set")
    parser.add_argument("--test_size", type=int, default=500, help="number of training set and validation set")
    parser.add_argument("--start_epoch", type=int, default=100, help="number of training set and validation set")
    parser.add_argument("--sample_num", type=int, default=5, help="number of training set and validation set")
    parser.add_argument("--LSF_UE", type=np.array, default=np.array([0.0,0.0],dtype=np.float32), help="Mean of path gains for K users")
    parser.add_argument("--Mainlobe_UE", type=np.array, default=np.array([0,0],dtype=np.float32), help="Center of the AoD range for K users")
    parser.add_argument("--HalfBW_UE", type=np.array, default= np.array([30.0,30.0],dtype=np.float32), help="Half of the AoD range for K users")
    parser.add_argument("--max_theta", type=float, default=60, help="Mean of path gains for K users")


    parser.add_argument("--annealing_rate", type=float, default=1.001, help="Annealing Rate")
    parser.add_argument("--annealing_rate_test", type=float, default=1, help="Annealing Rate param in testing")
    parser.add_argument("--annealing_rate_train", type=float, default=1, help="Annealing Rate Param in training")

    'System Parameter'
    parser.add_argument("--M", type=int, default=64, help="Antenna Number")
    parser.add_argument("--P_dl", type=int, default=1, help="POWER")
    parser.add_argument("--beta_tr", type=int, default=8, help="number of pilots")  # 'this is beta_tr'
    parser.add_argument("--K", type=int, default=6, help="number of users")
    parser.add_argument("--B", type=int, default=30, help="feedback capacity bits")
    parser.add_argument("--beta", type=int, default=0, help="the lagrangian multipler of objective function")
    parser.add_argument("--Lp_max", type=int, default=2, help="max number of path")
    parser.add_argument("--Lp_min", type=int, default=2, help="min number of path")
    parser.add_argument("--h_num", type=int, default=10, help="the number of collected previous UL channel samples")
    # parser.add_argument("--channel_sample", type=int, default=20, help="the instaneous samples of same geometry")
    parser.add_argument("--beta_fb", type=int, default=8, help="the feedback dimension") # can be tuned
    parser.add_argument("--snr_dl", type=int, default=10, help="SNR in dB")
    parser.add_argument("--kappa", type=float, default=1, help="ratio snr_ul /snr_dl not in dB")
    parser.add_argument("--T", type=int, default=70, help="the total number of dimension") # 14 * 5

    opt = parser.parse_args()
    # opt.sample_list = [5, 100]
    opt.LSF_UE = np.zeros(opt.K)
    opt.Mainlobe_UE = np.zeros(opt.K)
    opt.HalfBW_UE = opt.max_theta * np.ones(opt.K)
    return opt

# def Toep(X):
#     M = X.shape[0]
#     x = np.array([np.mean(np.diag(X, -j)) for j in range(M)])
#     x[0] = np.real(x[0])
#     X = toeplitz(x)
#     return X



def generate_batch_data(size, F_dl, M,K,L_min, L_max, LSF_UE, Mainlobe_UE, HalfBW_UE, theta_max,  N_ul, h_num=0):
    x_act = np.complex64(np.zeros((size, h_num, M, K))) # F^{\herm} @ h
    Sigma = np.complex64(np.zeros((size, h_num, M, K)))
    x_cov = np.complex64(np.zeros((size, h_num, M, M, K)))
    from0toM = np.float32(np.arange(0, M, 1))
    for size_idx in range(size):
        for kk in range(K):
            L = np.random.randint(L_max - L_min + 1) + L_min
            alpha_act = (np.random.randn(h_num, L) + 1j *np.random.randn(h_num, L))/np.sqrt(2)
            theta_act = (np.pi / 180) * np.random.uniform(low=Mainlobe_UE[kk]-HalfBW_UE[kk], high=Mainlobe_UE[kk]+HalfBW_UE[kk], size=[L, 1])
            gamma_input = np.random.uniform(0.5, 0.8, L)
            gamma_input = gamma_input/np.sum(gamma_input)
            diag_gamma = np.diag(np.sqrt(gamma_input))
            theta_act_expanded_temp = np.tile(theta_act,(1,M))
            #### UL and DL samples
            response_temp_DL = np.exp(-1j*np.pi*np.sin(theta_act_expanded_temp)/np.sin(theta_max/180*np.pi) * from0toM) ### dimension: L * M
            # response_temp_UL = np.exp(-1j * np.pi * 0.9 * np.sin(theta_act_expanded_temp) * from0toM)  ### dimension: L * M
            ####################################################current DL CSI ##################################
            h_dl = alpha_act @ diag_gamma @ response_temp_DL # h_num * M
            x_act[size_idx, :, :, kk] = h_dl @ F_dl.conj()

            Sigma_dl = np.transpose(response_temp_DL) @ np.diag(gamma_input) @ np.conjugate(response_temp_DL)
            x_cov[size_idx, :, :, :, kk] = np.tile(F_dl.conj().T @Sigma_dl @ F_dl, (h_num, 1, 1))
            Sigma[size_idx, :, :, kk] =  np.tile(Sigma_dl[:, 0], (h_num, 1))

    return x_act, x_cov, Sigma


class data_generation(Dataset):
    def __init__(self, test=True, train=False, **kwargs):
        # test data
        self.test = test
        self.train = train
        self.batch_per_epoch = kwargs['batch_num_per_epoch']
        self.batch_size = kwargs['batch_size']
        self.val_size= kwargs['val_size']
        self.test_size = kwargs['test_size']
        self.train_size = self.batch_size * self.batch_per_epoch
        self.M = kwargs['M']
        self.K = kwargs['K']
        self.Lp_min =kwargs['Lp_min']
        self.Lp_max = kwargs['Lp_max']
        self.h_num = kwargs['h_num']
        self.sample_per_file = kwargs['sample_per_file']
        self.sample_num = kwargs['sample_num']
        self.LSF_UE = kwargs['LSF_UE']
        self.Mainlobe_UE = kwargs['Mainlobe_UE']
        self.HalfBW_UE = kwargs['HalfBW_UE']
        self.theta_max = kwargs['max_theta']

        self.F_dl = np.complex64(np.fft.fft(np.eye(self.M)) / np.sqrt(self.M))

        if test:
            data_filename = './test_data_M_{}_K_{}_Lp_min_{}_Lp_max_{}_h_num_{}_sample_num_{}.npz'.format(
                self.M, self.K, self.Lp_min, self.Lp_max, 10, self.sample_num)
            data = np.load(data_filename)
            # load h
            self.h_act_test = data['x'][:self.test_size, :, :, :]
            self.hR_act_test = np.real(self.h_act_test)
            self.hI_act_test = np.imag(self.h_act_test)
            self.x_cov = data['x_cov_from_dl_Sigma'][:self.test_size, :, :, :, :]
            self.Sigma =  data['Sigma_dl'][:self.test_size, :, :, 0, :]
            self.num_entries = self.h_act_test.shape[0]
        else:
            if train:
                self.num_entries = self.train_size
            else:
                data_filename = './val_data_M_{}_K_{}_Lp_min_{}_Lp_max_{}_h_num_{}_sample_num_{}.npz'.format(
                    self.M, self.K, self.Lp_min, self.Lp_max, 10, self.sample_num)
                data = np.load(data_filename)
                # load h
                self.h_act_test = data['x'][:self.val_size, :, :, :]
                self.hR_act_test = np.real(self.h_act_test)
                self.hI_act_test = np.imag(self.h_act_test)
                self.x_cov = data['x_cov_from_dl_Sigma'][:self.val_size, :, :, :, :]
                self.Sigma = data['Sigma_dl'][:self.val_size, :, :, 0, :]
                self.num_entries = self.h_act_test.shape[0]


    def __getitem__(self, index):
        if self.train:
            x_act, x_cov, sigma = generate_batch_data(1, self.F_dl, self.M, self.K,
                                               self.Lp_min, self.Lp_max,
                                               self.LSF_UE, self.Mainlobe_UE, self.HalfBW_UE, self.theta_max,
                                               self.sample_num,
                                               self.h_num)
            self.hR_act_test = np.real(x_act)
            self.hI_act_test = np.imag(x_act)
            self.Sigma = sigma
            self.x_cov = x_cov
            self.num_entries = self.val_size
            return self.hR_act_test[0, :, :, :], self.hI_act_test[0, :,  :, :], self.x_cov[0, :, :, :, :], self.Sigma[0, :, :, :]
        else:
            return self.hR_act_test[index, :, :, :], self.hI_act_test[index, :,  :, :], self.x_cov[index, :, :, :, :], self.Sigma[index, :, :, :]

    def __len__(self):
        return self.num_entries



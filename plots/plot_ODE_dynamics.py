##
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import os
from tqdm import tqdm
from scipy.signal import find_peaks


main_path = os.path.join(os.path.split(os.getcwd())[0],'Epi_Social_Dynamic')
config_path = os.path.join(main_path,'config.csv')

config_data = pd.read_csv(config_path, sep=',', header=None, index_col=0)
results_path = config_data.loc['results_dir'][1]
plots_path = config_data.loc['plots_dir'][1]
parematric_df_dir = config_data.loc['parametric_df_dir'][1]
df_parametric = pd.read_csv(os.path.join(main_path, parematric_df_dir), index_col=0)

##
t_max = 300
gamma = 1 / 7
t = np.linspace(0, t_max, t_max*5)
min_prominence = 0.001

def count_oscillations(sim, min_prominence):
    idx_peaks, dict_peaks = find_peaks(sim, prominence=min_prominence)
    return idx_peaks, len(idx_peaks)

def find_stability_time(sim, epsilon):
    last_val = sim[-1,0]
    stable_sim = sim[np.abs(sim-last_val) <= epsilon]
    return len(stable_sim)  

def graph_simulationFeatures(path_to_results, name_file):
    df_temp = pd.read_csv(path_to_results+'.csv', index_col=0)
    I = np.array(df_temp[['I']]); S = np.array(df_temp[['S']])
    C = np.array(df_temp[['C']]); D = np.array(df_temp[['D']])
    time = np.array(df_temp[['time']])

    
    I_idxPeaks, I_numPeaks = count_oscillations(I[:,0], min_prominence)
    I_timeStable = find_stability_time(I, 0.0001)
    C_idxPeaks, C_numPeaks = count_oscillations(C[:,0], min_prominence)
    C_timeStable = find_stability_time(C, 0.0001)
    
    fig, axes = plt.subplots(2,1, figsize=(12,8))

    axes[0].plot(time, I, label='Infected', color='mediumorchid')
    axes[0].plot(time[-I_timeStable:], I[-I_timeStable:], label='final I = {:0.2f}'.format(I[-1,0]), color='mediumorchid', alpha=0.4, marker='o')
    axes[0].plot(time, S, label='Susceptible', color='dodgerblue')
    axes[0].scatter(time[np.argmax(I),0], np.max(I), label='Max. I = {:0.2f}'.format(np.max(I)), color='purple')
    axes[0].scatter(time[I_idxPeaks,0], I[I_idxPeaks,0], [500]*I_numPeaks, marker='|', label='# I Peaks = {:0.0f}'.format(I_numPeaks), color='indigo')
    axes[0].grid()
    axes[0].legend()
    axes[0].set_ylabel('Percentage [%]')
    axes[0].set_xlabel('Time [days]')

    axes[1].plot(time, C, label='Cooperators', color='limegreen')
    axes[1].plot(time[-C_timeStable:], C[-C_timeStable:], label='final C = {:0.2f}'.format(C[-1,0]), color='limegreen', alpha=0.4, marker='o')
    axes[1].plot(time, D, label='Defectors', color='orangered')
    axes[1].scatter(time[np.argmax(C)], np.max(C), label='Max. C = {:0.2f}'.format(np.max(C)), color='seagreen')
    axes[1].scatter(time[C_idxPeaks,0], C[C_idxPeaks,0], [500]*C_numPeaks, marker='|', label='# C Peaks = {:0.0f}'.format(C_numPeaks), color='darkgreen')
    axes[1].grid()
    axes[1].legend()
    axes[1].set_ylabel('Percentage [%]')
    axes[1].set_xlabel('Time [days]')

    plt.savefig(os.path.join(main_path, results_path, 'plots', 'ODE_Simulations', name_file+'.jpeg'), dpi=500)
    plt.close()

def graph_1D_experimentation(param_search, param_name:str):
    Imax_ = np.zeros(param_search.shape)
    Tmax_ = np.zeros(param_search.shape)
    Ifinal_ = np.zeros(param_search.shape)
    Cfinal_ = np.zeros(param_search.shape)
    Ioscillations_ = np.zeros(param_search.shape)
    Coscillations_ = np.zeros(param_search.shape)

    for idx1, p in enumerate(param_search):
        path_to_results = os.path.join(results_path, 'ode_results', '1D', 'ode_replicator_{}_{:0.2f}'.format(param_name, p)+'.csv')
        df_temp = pd.read_csv(path_to_results, index_col=0)
        
        Imax_[idx1] = np.max(df_temp[['I']])
        Tmax_[idx1] = np.array(df_temp[['time']])[np.argmax(df_temp[['I']])]
        Ifinal_[idx1] = np.array(df_temp[['I']])[-1]
        Cfinal_[idx1] = np.array(df_temp[['C']])[-1]
        Ioscillations_[idx1] = count_oscillations(np.array(df_temp[['I']])[:,0], min_prominence)[1]
        Coscillations_[idx1] = count_oscillations(np.array(df_temp[['C']])[:,0], min_prominence)[1]

    fig, ax = plt.subplots(2, 3, figsize=(14,10))

    ax[0,0].plot(param_search, Imax_)
    ax[0,0].set_title('Max. Infected')
    ax[0,0].grid()

    ax[1,0].plot(param_search, Tmax_)
    ax[1,0].set_xlabel(f'{param_name}')
    ax[1,0].set_title('Max. Infected Time')
    ax[1,0].grid()
    
    ax[0,1].plot(param_search, Ifinal_)
    ax[0,1].set_title('Final Infected')
    ax[0,1].grid()
    
    ax[1,1].plot(param_search, Cfinal_)
    ax[1,1].grid()
    ax[1,1].set_xlabel(f'{param_name}')
    ax[1,1].set_title('Final Cooperators')

    ax[0,2].plot(param_search, Ioscillations_)
    ax[0,2].grid()
    ax[0,2].set_title('# Peaks of Infected')

    ax[1,2].plot(param_search, Coscillations_)
    ax[1,2].grid()
    ax[1,2].set_xlabel(f'{param_name}')
    ax[1,2].set_title('# Peaks of Cooperators')

    if not os.path.isdir( os.path.join(results_path, plots_path, '1D') ):
                os.makedirs(os.path.join(results_path, plots_path, '1D'))
    
    plt.savefig(os.path.join(results_path, plots_path, '1D','plot_features_{}_exp.jpeg'.format(param_name)))
    plt.close()

def graph_2D_experimentation(param_search1, param_search2, param_name1: str, param_name2: str):
    Imax_ = np.zeros((param_search1.shape[0], param_search2.shape[0]))
    Tmax_ = np.zeros((param_search1.shape[0], param_search2.shape[0]))
    Ifinal_ = np.zeros((param_search1.shape[0], param_search2.shape[0]))
    Cfinal_ = np.zeros((param_search1.shape[0], param_search2.shape[0]))
    Ioscillations_ = np.zeros((param_search1.shape[0], param_search2.shape[0]))
    Coscillations_ = np.zeros((param_search1.shape[0], param_search2.shape[0]))

    param_ticks1 = np.linspace(param_search1[0], param_search1[-1], 6)
    param_ticks2 = np.linspace(param_search2[0], param_search2[-1], 6)

    for idx1, p1 in enumerate(param_search1):
        df_temp = df_parametric[[param_name1]]
        param_search1 = np.linspace(df_temp.loc['min'][0], df_temp.loc['max'][0], int(df_temp.loc['num'][0]))

        for idx2, p2 in enumerate(param_search2):
            path_to_results = os.path.join(results_path, 'ode_results', '2D', 'ode_replicator_{}_{:0.2f}_{}_{:0.2f}'.format(param_name1, p1, param_name2, p2)+'.csv')
            df_temp = pd.read_csv(path_to_results, index_col=0)

            Imax_[idx1, idx2] = np.max(df_temp[['I']])
            Tmax_[idx1, idx2] = np.array(df_temp[['time']])[np.argmax(df_temp[['I']])]
            Ifinal_[idx1, idx2] = np.array(df_temp[['I']])[-1]
            Cfinal_[idx1, idx2] = np.array(df_temp[['C']])[-1]
            Ioscillations_[idx1, idx2] = count_oscillations(np.array(df_temp[['I']])[:,0], 0.001)[1]
            Coscillations_[idx1, idx2] = count_oscillations(np.array(df_temp[['C']])[:,0], 0.001)[1]
        
    fig, axes = plt.subplots(2, 3, figsize=(14,10))
    
    #heatmaps
    im1 = axes[0,0].matshow(Imax_, cmap='coolwarm')
    im2 = axes[1,0].matshow(Tmax_, cmap='coolwarm')
    im3 = axes[0,1].matshow(Ifinal_, cmap='coolwarm')
    im4 = axes[1,1].matshow(Cfinal_, cmap='coolwarm')
    im5 = axes[0,2].matshow(Ioscillations_, cmap='coolwarm')
    im6 = axes[1,2].matshow(Coscillations_, cmap='coolwarm')

    #axes[0,0].set_xticks(range(len(param_ticks2)))
    #axes[0,0].set_yticks(range(len(param_ticks1)))
    #axes[0,0].set_xticklabels(param_ticks2)
    #axes[0,0].set_yticklabels(param_ticks1)
    axes[0,0].set_title('Final Infected', y=-0.1)
    axes[0,0].set_ylabel(f'{param_name1}')
    plt.setp(axes[0,0].get_xticklabels(), ha='left')
    plt.colorbar(im1, fraction=0.045, pad=0.05, ax=axes[0,0])

    #axes[1,0].set_xticks(range(len(param_ticks2)))
    #axes[1,0].set_yticks(range(len(param_ticks1)))
    #axes[1,0].set_xticklabels(param_ticks2)
    #axes[1,0].set_yticklabels(param_ticks1)
    axes[1,0].set_title('Final Cooperators', y=-0.1)
    axes[1,0].set_ylabel(f'{param_name1}')
    axes[1,0].set_xlabel(f'{param_name2}')
    plt.setp(axes[1,0].get_xticklabels(), ha='left')
    plt.colorbar(im2, fraction=0.045, pad=0.05, ax=axes[1,0])
    
    #axes[0,1].set_xticks(range(len(param_ticks2)))
    #axes[0,1].set_yticks(range(len(param_ticks1)))
    #axes[0,1].set_xticklabels(param_ticks2)
    #axes[0,1].set_yticklabels(param_ticks1)
    axes[0,1].set_title('Max. Infected', y=-0.1)
    plt.setp(axes[0,1].get_xticklabels(), ha='left')
    plt.colorbar(im3, fraction=0.045, pad=0.05, ax=axes[0,1])

    #axes[1,1].set_xticks(range(len(param_ticks2)))
    #axes[1,1].set_yticks(range(len(param_ticks1)))
    #axes[1,1].set_xticklabels(param_ticks2)
    #axes[1,1].set_yticklabels(param_ticks1)
    axes[1,1].set_title('Max. Infected Time', y=-0.1)
    axes[1,1].set_xlabel(f'{param_name2}')
    plt.setp(axes[1,1].get_xticklabels(), ha='left')
    plt.colorbar(im4, fraction=0.045, pad=0.05, ax=axes[1,1])

    #axes[0,2].set_xticks(range(len(param_ticks2)))
    #axes[0,2].set_yticks(range(len(param_ticks1)))
    #axes[0,2].set_xticklabels(param_ticks2)
    #axes[0,2].set_yticklabels(param_ticks1)
    axes[0,2].set_title('# Peaks of Infected', y=-0.1)
    plt.setp(axes[0,2].get_xticklabels(), ha='left')
    plt.colorbar(im5, fraction=0.045, pad=0.05, ax=axes[0,2])

    #axes[1,2].set_xticks(range(len(param_ticks2)))
    #axes[1,2].set_yticks(range(len(param_ticks1)))
    #axes[1,2].set_xticklabels(param_ticks2)
    #axes[1,2].set_yticklabels(param_ticks1)
    axes[1,2].set_title('# Peaks of Cooperators', y=-0.1)
    axes[1,2].set_xlabel(f'{param_name2}')
    plt.setp(axes[1,2].get_xticklabels(), ha='left')
    plt.colorbar(im6, fraction=0.045, pad=0.05, ax=axes[1,2])

    fig.tight_layout()

    if not os.path.isdir( os.path.join(results_path, plots_path, '2D') ):
                os.makedirs(os.path.join(results_path, plots_path, '2D'))
    

    plt.savefig(os.path.join(results_path, plots_path, '2D','heatmap_features_{}_{}_exp.jpeg'.format(param_name1,param_name2)))
    plt.close()


sim1_path = os.path.join(main_path, results_path, 'ode_results','1D', 'ode_replicator_beta_0.33')           
sim2_path = os.path.join(main_path, results_path, 'ode_results','1D', 'ode_replicator_beta_0.79')
sim3_path = os.path.join(main_path, results_path, 'ode_results','1D', 'ode_replicator_sigmaC_0.33')
sim4_path = os.path.join(main_path, results_path, 'ode_results','1D', 'ode_replicator_sigmaC_0.79')
sim5_path = os.path.join(main_path, results_path, 'ode_results','1D', 'ode_replicator_sigmaD_0.33')
sim6_path = os.path.join(main_path, results_path, 'ode_results','1D', 'ode_replicator_sigmaD_0.79')

graph_simulationFeatures(sim1_path, 'ode_replicator_beta_0.33')
graph_simulationFeatures(sim2_path, 'ode_replicator_beta_0.79')
graph_simulationFeatures(sim3_path, 'ode_replicator_sigmaC_0.33')
graph_simulationFeatures(sim4_path, 'ode_replicator_sigmaC_0.79')
graph_simulationFeatures(sim5_path, 'ode_replicator_sigmaD_0.33')
graph_simulationFeatures(sim6_path, 'ode_replicator_sigmaD_0.79')



beta_ = df_parametric[['beta']]
sigmaD_ = df_parametric[['sigmaD']]
sigmaC_ = df_parametric[['sigmaC']]
list_params = ['beta', 'sigmaD', 'sigmaC']

beta_search = np.linspace(beta_.loc['min'][0], beta_.loc['max'][0], int(beta_.loc['num'][0]))
sigmaD_search = np.linspace(sigmaD_.loc['min'][0], sigmaD_.loc['max'][0], int(sigmaD_.loc['num'][0]))
sigmaC_search = np.linspace(sigmaC_.loc['min'][0], sigmaC_.loc['max'][0], int(sigmaC_.loc['num'][0]))

graph_1D_experimentation(beta_search, 'beta')
graph_1D_experimentation(sigmaD_search, 'sigmaD')
graph_1D_experimentation(sigmaC_search, 'sigmaC')


for idx1, param_name1 in enumerate(list_params):
        df_temp = df_parametric[[param_name1]]
        param_search1 = np.linspace(df_temp.loc['min'][0], df_temp.loc['max'][0], int(df_temp.loc['num'][0]))

        list_temp = list_params.copy()
        list_temp.remove(param_name1)
        for idx2, param_name2 in enumerate(list_temp):
            df_temp = df_parametric[[param_name2]]
            param_search2 = np.linspace(df_temp.loc['min'][0], df_temp.loc['max'][0], int(df_temp.loc['num'][0]))
            graph_2D_experimentation(param_search1, param_search2, param_name1, param_name2)
        


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import os
from tqdm import tqdm

main_path = os.path.join(os.path.split(os.getcwd())[0],'Epi_Social_Dynamic')
config_path = os.path.join(main_path, 'config.csv')
config_data = pd.read_csv(config_path, sep=',', header=None, index_col=0)
results_path  = config_data.loc['results_dir'][1]
plots_path = config_data.loc['plots_dir'][1]
parematric_df_dir = config_data.loc['parametric_df_dir'][1]
gamma = 1/7
alpha = 0.2
reward_matrix = np.array([[1.1, 1.1, 0.8, 0.7], [1.3, 1.3, 0.5, 0.3], [2, 1.8, 1, 1], [1.6, 1.4, 1, 1]])

def SIS_coupled(variables, t, beta_max, alpha, gamma, A, sigmaD, sigmaC, selfcare:bool=True, public_awareness:bool=True, dynamic_I:bool= True, dynamic_S:bool=True):
    global N

    S_c, S_d, I_c, I_d = variables

    beta = beta_max*np.exp(-(S_c + I_c))

    S_total = S_c + S_d 
    I_total = I_c + I_d 

    penalization_Sc = 0
    penalization_Sd = 0
    penalization_Ic = 0
    penalization_Id = 0

    if selfcare:
        penalization_Sc = sigmaC*(S_total)
        penalization_Sd = sigmaD*(I_total)
    if public_awareness:
        penalization_Ic = sigmaC*(S_total)
        penalization_Id = sigmaD*(I_total)
    
    f_sc = A[0,0]*S_c + A[0,1]*S_d + (A[0,2]-penalization_Sc)*I_c + (A[0,3]-sigmaC*(S_total))*I_d
    f_sd = A[1,0]*S_c + A[1,1]*S_d + (A[1,2]-penalization_Sd)*I_c + (A[1,3]-penalization_Sd)*I_d
    f_ic = A[2,0]*S_c + A[2,1]*S_d + (A[2,2]-penalization_Ic)*I_c + (A[2,3]-penalization_Ic)*I_d
    f_id = A[3,0]*S_c + A[3,1]*S_d + (A[3,2]-penalization_Id)*I_c + (A[3,3]-penalization_Id)*I_d
    
    fbar_s = f_sc*(S_c/S_total) + f_sd*(S_d/S_total)
    fbar_i = f_ic*(I_c/I_total) + f_id*(I_d/I_total)

    dS_cdt = -beta*S_c*(I_d + alpha*I_c) + gamma*I_c 
    dI_cdt = beta*S_c*(I_d + alpha*I_c) - gamma*I_c 
    dS_ddt = -beta*S_d*(I_d + alpha*I_c) + gamma*I_d 
    dI_ddt = beta*S_d*(I_d + alpha*I_c) - gamma*I_d 

    if dynamic_S:
        dS_cdt += S_c*(f_sc - fbar_s)
        dS_ddt += S_d*(f_sd - fbar_s)
    if dynamic_I:
        dI_cdt += I_c*(f_ic - fbar_i)
        dI_ddt += I_d*(f_id - fbar_i)
         
    
    

    return [dS_cdt, dS_ddt, dI_cdt, dI_ddt]

def run_sims_SIS_coupled(prob_infect, alpha, A, sigmaD, sigmaC:float=0):
    defectFract = 0.9
    coopFract = 1 - defectFract
    N = 5000
    I = 2
    S = N - I
    S_c = S*coopFract
    S_d = S*defectFract
    I_c = I*coopFract
    I_d = I*defectFract

    y0 = [S_c/N, S_d/N, I_c/N, I_d/N]

    t_max = 300
    t = np.linspace(0, t_max, t_max*5)
    gamma = 1/7

    y = odeint(SIS_coupled, y0, t, args=(prob_infect, alpha, gamma, A, sigmaD, sigmaC))
    S_c_ = y[:,0]
    S_d_ = y[:,1]
    I_c_ = y[:,2]
    I_d_ = y[:,3]

    pd_var = pd.DataFrame(columns=['time', 'beta', 'alpha', 'sigma_D', 'sigma_C', 'S_c', 'S_d', 'I_c', 'I_d'])
    pd_var['time'] = t
    pd_var['beta'] = prob_infect
    pd_var['alpha'] = alpha
    pd_var['sigma_D'] = sigmaD
    pd_var['sigma_C'] = sigmaC
    pd_var['S_c'] = S_c_
    pd_var['S_d'] = S_d_
    pd_var['I_c'] = I_c_
    pd_var['I_d'] = I_d_

    return pd_var

def exp_1D_SIS_coupled(param_search1, param1:str):
    if not os.path.isdir( os.path.join(results_path, 'ode_results', '1D') ):
                os.makedirs(os.path.join(results_path, 'ode_results', '1D'))

    beta_mean = beta_.loc['mean'][0]
    sigmaD_mean = sigmaD_.loc['mean'][0]
    sigmaC_mean = sigmaC_.loc['mean'][0]

    if param1 == 'beta':    
        for idx, p in tqdm(enumerate(param_search1)):
            pd_var_res = run_sims_SIS_coupled(p, alpha, reward_matrix, sigmaD_mean, sigmaC_mean)
            pd_var_res_ = pd_var_res.copy()
            
            pd_var_res_.to_csv(os.path.join(results_path, 
    '1D','ode_coupled_beta_{:0.2f}_sigmaD_{:0.2f}_sigmaC_{:0.2f}.csv'.format(p, sigmaD_mean, sigmaC_mean)))
        print('DONE beta EXPERIMENTATION')
    elif param1 == 'sigmaD':
        for idx, p in tqdm(enumerate(param_search1)):
            pd_var_res = run_sims_SIS_coupled(beta_mean, alpha, reward_matrix, p, sigmaC_mean)
            pd_var_res_ = pd_var_res.copy()
            
            pd_var_res_.to_csv(os.path.join(results_path, 
    '1D','ode_coupled_beta_{:0.2f}_sigmaD_{:0.2f}_sigmaC_{:0.2f}.csv'.format(beta_mean, p, sigmaC_mean)))    
        print('DONE sigmaD EXPERIMENTATION')
    elif param1 == 'sigmaC':
        for idx, p in tqdm(enumerate(param_search1)):
            pd_var_res = run_sims_SIS_coupled(beta_mean, alpha, reward_matrix, sigmaD_mean, p)
            pd_var_res_ = pd_var_res.copy()
            
            pd_var_res_.to_csv(os.path.join(results_path,
    '1D','ode_coupled_beta_{:0.2f}_sigmaD_{:0.2f}_sigmaC_{:0.2f}.csv'.format(beta_mean, sigmaD_mean, p)))
        print('DONE sigmaC EXPERIMENTATION')

def exp_2D_SIS_coupled(param_search1, param_search2, param1: str, param2: str):
    if not os.path.isdir( os.path.join(results_path, 'ode_results', '2D') ):
                os.makedirs(os.path.join(results_path, 'ode_results', '2D'))
    
    beta_mean = beta_.loc['mean'][0]
    sigmaD_mean = sigmaD_.loc['mean'][0]
    sigmaC_mean = sigmaC_.loc['mean'][0]
    
    if param1 == 'beta':
        if param2 == 'sigmaD':
            for idx1, p1 in tqdm(enumerate(param_search1)):
                 for idx2, p2 in tqdm(enumerate(param_search2)):
                        pd_var_res = run_sims_SIS_coupled(p1, alpha, reward_matrix,p2,sigmaC_mean)
                        pd_var_res_ = pd_var_res.copy()
            
                        pd_var_res_.to_csv(os.path.join(results_path, 
            '2D','ode_coupled_beta_{:0.2f}_sigmaD_{:0.2f}_sigmaC_{:0.2f}.csv'.format(p1,p2, sigmaC_mean)))
        elif param2 == 'sigmaC':
             for idx1, p1 in tqdm(enumerate(param_search1)):
                 for idx2, p2 in tqdm(enumerate(param_search2)):
                        pd_var_res = run_sims_SIS_coupled(p1, alpha, reward_matrix,sigmaD_mean,p2)
                        pd_var_res_ = pd_var_res.copy()
            
                        pd_var_res_.to_csv(os.path.join(results_path, 
            '2D','ode_coupled_beta_{:0.2f}_sigmaD_{:0.2f}_sigmaC_{:0.2f}.csv'.format(p1,sigmaD_mean,p2)))

    elif param1 == 'sigmaD':
        if param2 == 'beta':
            for idx1, p1 in tqdm(enumerate(param_search1)):
                for idx2, p2 in tqdm(enumerate(param_search2)):
                    pd_var_res = run_sims_SIS_coupled(p2,alpha,reward_matrix,p1,sigmaC_mean)
                    pd_var_res_ = pd_var_res.copy()
            
                    pd_var_res_.to_csv(os.path.join(results_path, 
            '2D','ode_coupled_beta_{:0.2f}_sigmaD_{:0.2f}_sigmaC_{:0.2f}.csv'.format(p2,p1,sigmaC_mean)))

        elif param2 == 'sigmaC':
            for idx1, p1 in tqdm(enumerate(param_search1)):
                for idx2, p2 in tqdm(enumerate(param_search2)):
                    pd_var_res = run_sims_SIS_coupled(beta_mean,alpha,reward_matrix,p1,p2)
                    pd_var_res_ = pd_var_res.copy()
            
                    pd_var_res_.to_csv(os.path.join(results_path, 
            '2D','ode_coupled_beta_{:0.2f}_sigmaD_{:0.2f}_sigmaC_{:0.2f}.csv'.format(beta_mean,p1,p2)))

    elif param1 == 'sigamC':
        if param2 == 'beta':
            for idx1, p1 in tqdm(enumerate(param_search1)):
                for idx2, p2 in tqdm(enumerate(param_search2)):
                    pd_var_res = run_sims_SIS_coupled(p2,alpha,reward_matrix,sigmaD_mean,p1)
                    pd_var_res_ = pd_var_res.copy()
            
                    pd_var_res_.to_csv(os.path.join(results_path, 
            '2D','ode_coupled_beta_{:0.2f}_sigmaD_{:0.2f}_sigmaC_{:0.2f}.csv'.format(p2,sigmaD_mean,p1)))

        elif param2 == 'sigmaD':
            for idx1, p1 in tqdm(enumerate(param_search1)):
                for idx2, p2 in tqdm(enumerate(param_search2)):
                    pd_var_res = run_sims_SIS_coupled(beta_mean,alpha,reward_matrix, p2, p1)
                    pd_var_res_ = pd_var_res.copy()
            
                    pd_var_res_.to_csv(os.path.join(results_path, 
            '2D','ode_coupled_beta_{:0.2f}_sigmaD_{:0.2f}_sigmaC_{:0.2f}.csv'.format(beta_mean,p2,p1)))


df_parametric = pd.read_csv(os.path.join(main_path, parematric_df_dir), index_col=0)
beta_ = df_parametric[['beta']]
sigmaD_ = df_parametric[['sigmaD']]
sigmaC_ = df_parametric[['sigmaC']]

list_values = ['low', 'mean', 'high']

for idx1, val1 in enumerate(list_values):
    fig, ax = plt.subplots(3,3, figsize=(14,10))
    beta_temp = beta_.loc[val1][0]
    plt.suptitle(f'${{\\beta}}$ = {beta_temp}')
    for idx2, val2 in enumerate(list_values):
        sigmaD_temp = sigmaD_.loc[val2][0]
        for idx3, val3 in enumerate(list_values):
            sigmaC_temp = sigmaC_.loc[val3][0]
            pd_temp = run_sims_SIS_coupled(beta_temp,alpha, reward_matrix, sigmaD_temp, sigmaC_temp)

            ax[idx2, idx3].plot(pd_temp['time'], pd_temp['I_d'], label='Infected-Defector')
            ax[idx2,idx3].plot(pd_temp['time'], pd_temp['S_d'], label='Susceptible-Defector')
            ax[idx2, idx3].plot(pd_temp['time'], pd_temp['I_c'], label='Infected-Cooperator')
            ax[idx2,idx3].plot(pd_temp['time'], pd_temp['S_c'], label='Susceptible-Cooperator')
            ax[idx2,idx3].grid()
            ax[idx2,idx3].legend()

            if idx2 == 0:
                ax[idx2,idx3].set_title(f'${{\sigma_D}}$ = {sigmaC_temp}') 
            if idx3 == 0:
                ax[idx2,idx3].set_ylabel(f'${{\sigma_C}}$ = {sigmaD_temp} \n Fraction') 
            if idx2 == 2:
                ax[idx2,idx3].set_xlabel('Time [days]') 

    if not os.path.isdir( os.path.join(plots_path, 'ODE_Simulations') ):
                os.makedirs(os.path.join(plots_path, 'ODE_Simulations'))
    
    plt.savefig(os.path.join(plots_path, 'ODE_Simulations',
                             'simu_ode_coupled_beta_{:0.2f}.jpeg'.format(beta_temp)), dpi=400)
    plt.close()

print('DONE SIMPLE SIMULATIONS')

### Save results

list_params = ['beta', 'sigmaD', 'sigmaC']

for idx, param_name in enumerate(list_params):
    df_temp = df_parametric[[param_name]]
    param_search = np.linspace(df_temp.loc['min'][0], df_temp.loc['max'][0], int(df_temp.loc['num'][0]))
    exp_1D_SIS_coupled(param_search, param_name)

print('DONE 1D Experimentations')

for idx1, param_name1 in enumerate(list_params):
    df_temp = df_parametric[[param_name1]]
    param_search1 = np.linspace(df_temp.loc['min'][0], df_temp.loc['max'][0], int(df_temp.loc['num'][0]))

    list_temp = list_params.copy()
    list_temp.remove(param_name1)
    for idx2, param_name2 in enumerate(list_temp):
        df_temp = df_parametric[[param_name2]]
        param_search2 = np.linspace(df_temp.loc['min'][0], df_temp.loc['max'][0], int(df_temp.loc['num'][0]))

        exp_2D_SIS_coupled(param_search1, param_search2, param_name1, param_name2)
        print(f'Finish {param_name1}-{param_name2} Experimentation')

print('DONE 2D Experimentations')



#TODO Finish this function
#def exp_3D_SIS_replicator():







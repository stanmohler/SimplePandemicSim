# Rough simulation of the COVID-19 pandemic in the US
# by Stan Mohler, 12/2020
# Inspired by https://forum.bayesia.us/t/p8hymxb/webinar-series-reasoning-under-uncertainty-part-3-epidemic-modeling-with-temporal-bayesian-networks
#         and https://phys.org/news/2020-03-mathematical-epidemiology-pandemic.html

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

def plot_scenarios(scenarios, do_log_plot=False):

    # find the duration of the longest scenario

    num_days_to_plot = 0
    for scenario in scenarios:
        num_days_to_plot = max(num_days_to_plot, scenario.get('pandemic_duration_days'))

    # extend all scenarios to longest duration of any of them
    
    for scenario in scenarios:

        num_days_to_extend_by = num_days_to_plot - scenario.get('pandemic_duration_days')

        scenario['num_susceptible'] += num_days_to_extend_by * [ scenario.get('num_susceptible')[-1] ]
        scenario['num_infected']    += num_days_to_extend_by * [ scenario.get('num_infected')[-1] ]
        scenario['num_recovered']   += num_days_to_extend_by * [ scenario.get('num_recovered')[-1] ]
        scenario['num_dead']        += num_days_to_extend_by * [ scenario.get('num_dead')[-1] ]

    # prepare to plot

    plt.rcParams['figure.figsize'] = 9,6
    fig, axs = plt.subplots(2, 2)

    fig.suptitle('Simple Pandemic Simulation by Stan Mohler, Jr.', fontsize=8)

    axs[0,0].set_title('Susceptable')
    axs[0,1].set_title('Infected (Infectious)')
    axs[1,0].set_title('Recovered (Immune)')
    axs[1,1].set_title('Deaths')

    # plot each scenario

    for scenario in scenarios:

        num_days  = num_days_to_plot # scenario.get('pandemic_duration_days')
        x         = np.linspace( 0, num_days, num=num_days )
        lbl       = scenario.get('name')
        s         = scenario.get('num_susceptible')
        i         = scenario.get('num_infected')
        r         = scenario.get('num_recovered')
        d         = scenario.get('num_dead')
        linestyle = scenario.get('linestyle')

        axs[0,0].plot(x, s, 'tab:blue',   linestyle=linestyle, label=lbl)
        axs[0,1].plot(x, i, 'tab:orange', linestyle=linestyle, label=lbl)
        axs[1,0].plot(x, r, 'tab:green',  linestyle=linestyle, label=lbl)
        axs[1,1].plot(x, d, 'tab:red',    linestyle=linestyle, label=lbl)

    # show the legends

    if len(scenarios) > 1:
        axs[0,0].legend(bbox_to_anchor=(0.98, 0.2),  loc='lower right', borderaxespad=0.02, fontsize='xx-small')
        axs[0,1].legend(bbox_to_anchor=(0.98, 0.98), loc='upper right', borderaxespad=0.02, fontsize='xx-small')
        axs[1,0].legend(bbox_to_anchor=(0.98, 0.6),  loc='lower right', borderaxespad=0.02, fontsize='xx-small')
        axs[1,1].legend(bbox_to_anchor=(0.98, 0.6),  loc='lower right', borderaxespad=0.02, fontsize='xx-small')
    else:
        fig.suptitle('Simple Pandemic Simulation by Stan Mohler, Jr.\n' + scenarios[0].get('name'), fontsize=8)

    # format the plot, show it

    for ax in axs.flat:
        if do_log_plot:
            ax.set(xlabel='days', ylabel='log of no. people')
            ax.grid(axis='y')
            ax.set_yscale('log')
        else:
            ax.set(xlabel='days', ylabel='no. people')             
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    plt.subplots_adjust(left=0.2, bottom=None, right=None, top=0.83, wspace=0.6, hspace=0.5)

    # TODO - could use the code below
    #axs[0,1].annotate('infection gone', xy=(herd_immunity_day[0], 0), xytext=(herd_immunity_day[0]-300, 50e6),
    #            arrowprops=dict(facecolor='black', shrink=0.05),
    #            )

    plt.show()


def simulate_scenario(scenario_name, R0, plot_linestyle):
    
    print(f'Scenario name: {scenario_name}')
    print(f'R0 = {R0}')
    
    num_susceptible = [ float(330e6 - 1) ]
    num_infected    = [ float(1) ]
    num_recovered   = [ float(0) ]
    num_dead        = [ float(0) ]
    
    num_got_infected_today  = [ float(1) ]
    num_recovered_today     = [ float(0) ]
    num_died_today          = [ float(0) ]

    print(f'Day 0: {num_recovered_today[-1]:.1f} recovered,  {num_died_today[-1]:.1f} died.  S={num_susceptible[-1]:.1f}  I={num_infected[-1]:.1f}  R={num_recovered[-1]:.1f}  D={num_dead[-1]:.1f}')
    
    day = 0
    
    while num_infected[-1] > 0 and day < 1000:
        
        day += 1
        
        # current Reproduction Number drops with no. susceptible
        Rt = R0 * num_susceptible[-1] / 330e6
        
        # each infected person infects their Rt-many 'victims' over 14 days
        num_got_infected_today.append( num_infected[-1] * Rt / 14 )
        
        if day < 14:  # then no one has been sick long enough to recover
            
            num_recovered_today.append(0)
            num_died_today.append(0)
            
        else:  # most of the people who got sick 14 days ago
               # recover today, but a few die
            
            num_recovered_today.append( 0.99 * num_got_infected_today[-15])
            num_died_today.append(      0.01 * num_got_infected_today[-15])
            
        num_infected.append( num_infected[-1] + num_got_infected_today[-1] - num_recovered_today[-1] - num_died_today[-1])
        num_susceptible.append( num_susceptible[-1] - num_got_infected_today[-1])
        num_recovered.append( num_recovered[-1] + num_recovered_today[-1])
        num_dead.append( num_dead[-1] + num_died_today[-1])

        if num_infected[-1] < 1.0:  # then only  'fraction of a person' is now infected, so round down to 0
            num_infected[-1] = 0
        
        #print(f'Day {day}: {num_recovered_today[-1]:.1f} recovered,  {num_died_today[-1]:.1f} died.  S={num_susceptible[-1]:.1f}  I={num_infected[-1]:.1f}  R={num_recovered[-1]:.1f}  D={num_dead[-1]:.1f}')
        
    #print(f'Day {day}: Infection gone')

    scenario = {
        'name':                    scenario_name,
        'R0':                      R0,
        'num_susceptible':         num_susceptible,
        'num_infected':            num_infected,
        'num_recovered':           num_recovered,
        'num_dead':                num_dead,
        'pandemic_duration_days':  len(num_infected),
        'linestyle':               plot_linestyle
    }

    return scenario
    
###############################################################################################

normal_life              = simulate_scenario('Normal Life',              2.5,  'dotted')
mild_social_distancing   = simulate_scenario('Mild Social Distancing',   1.25, 'solid')
strong_social_distancing = simulate_scenario('Strong Social Distancing', 1.1,  'dashed')

# see linestyles at https://matplotlib.org/3.1.0/gallery/lines_bars_and_markers/linestyles.html

plot_scenarios( [normal_life, mild_social_distancing, strong_social_distancing], do_log_plot=False)

plot_scenarios( [mild_social_distancing], do_log_plot=True)

print('DONE')
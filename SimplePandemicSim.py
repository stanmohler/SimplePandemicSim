# Rough simulation of the COVID-19 pandemic in the US
# by Stan Mohler, 9/2020
# Inspired by https://forum.bayesia.us/t/p8hymxb/webinar-series-reasoning-under-uncertainty-part-3-epidemic-modeling-with-temporal-bayesian-networks

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

NUM_DAYS_SIMULATED                 = 1000
NUM_DAYS_INFECTIOUS                = 14
DEATH_RATE                         = 0.01
MIN_DAYS_IMMUNE                    = 60
FRACTION_WHO_LOSE_IMMUNITY         = 0  # 0.4
TOTAL_POPULATION                   = 330e6
INITIAL_NUM_INFECTIONS             = 1

LOW_INITIAL_REPRODUCTION_NUMBER    = 1.25    # R0, the initial no. of people each contagious person infects
HIGH_INITIAL_REPRODUCTION_NUMBER   = 2.5     # R0 for less social distancing
MAX_DAYS_SOCIAL_DISTANCING         = 9999

# initialize arrays to store all scenarios
num_susceptible_arry_arry         = []
num_infectious_arry_arry          = []
num_immune_arry_arry              = []
num_dead_arry_arry                = []

herd_immunity_day = []
total_dead = []

# LOOP OVER SCENARIOS WITH DIFFERENT REPRODUCTION RATES

for s in range(2):

    infection_dissipating = False
    infection_gone = False

    initial_reproduction_number = LOW_INITIAL_REPRODUCTION_NUMBER
    if s == 1:
        initial_reproduction_number = HIGH_INITIAL_REPRODUCTION_NUMBER

    print(f'\n\nSCENARIO {s+1} OF 2: Initial reproduction no. = {initial_reproduction_number}')

    # set initial values of the 4 quantities to compute and plot
    num_susceptible = TOTAL_POPULATION - INITIAL_NUM_INFECTIONS
    num_infectious  = INITIAL_NUM_INFECTIONS
    num_immune      = 0
    num_dead        = 0

    # initialize arrays to store the time history of the quantities for one scenario
    num_susceptible_arry     = [num_susceptible]
    num_infectious_arry      = [num_infectious]
    num_immune_arry          = [num_immune]
    num_dead_arry            = [num_dead]
    num_infected_today_arry  = [num_infectious]
    num_recovered_today_arry = [0]

    # LOOP OVER THE DAYS BEING SIMULATED

    t_10_deaths = None

    for t in range(NUM_DAYS_SIMULATED):

        if num_infectious == 0 and not infection_gone: # and initial_reproduction_number < HIGH_INITIAL_REPRODUCTION_NUMBER:
            infection_gone = True
            
            if initial_reproduction_number < HIGH_INITIAL_REPRODUCTION_NUMBER:
                initial_reproduction_number = HIGH_INITIAL_REPRODUCTION_NUMBER 
                herd_immunity_day.append(t)
                total_dead.append(num_dead)
                percent_immune = 100 * num_immune / (TOTAL_POPULATION - num_dead)
                print(f'Day {t+1:4}: INFECTION GONE.  {num_dead:.0f} dead.  {percent_immune:.0f}% immune.  ENDING SOCIAL DISTANCING.')

            else:
                herd_immunity_day.append(t)
                total_dead.append(num_dead)
                percent_immune = 100 * num_immune / (TOTAL_POPULATION - num_dead)
                print(f'Day {t+1:4}: INFECTION GONE.  {num_dead:.0f} dead.  {percent_immune:.0f}% immune.')

        # after a long time, both scenarios go to the high reproduction number
        if t >= MAX_DAYS_SOCIAL_DISTANCING and initial_reproduction_number < HIGH_INITIAL_REPRODUCTION_NUMBER:
            print(f'Day {t+1:4}: HIT LIMIT ON DAYS TO SOCIAL DISTANCE.')
            initial_reproduction_number = HIGH_INITIAL_REPRODUCTION_NUMBER

        # sick people infect others in proportion to how many are susceptible
        effective_reproduction_number = initial_reproduction_number * num_susceptible / num_susceptible_arry[0]

        # check whether virus is dissipating
        if not infection_dissipating and effective_reproduction_number < 1.0:
            infection_dissipating = True
            percent_immune = 100 * num_immune / (TOTAL_POPULATION - num_dead)
            print(f'Day {t+1:4}: VIRUS IS DISSIPATING: Reproduction number < 1.  {percent_immune:.0f}% immune.')

        # each sick person infects their "victims" over several days
        num_infected_today = num_infectious * effective_reproduction_number / NUM_DAYS_INFECTIOUS

        # set default values, which might change farther below
        num_recovered_today     = 0.0
        num_deaths_today        = 0.0
        num_lost_immunity_today = 0.0
        
        if t >= NUM_DAYS_INFECTIOUS:
            # then some infectious people lose their infectiousness today.  
            # How many?  The no. who became infectious NUM_DAYS_INFECTIOUS days ago.  
            num_losing_infectiousness = num_infected_today_arry[ t - NUM_DAYS_INFECTIOUS ]
            num_recovered_today = (1.0 - DEATH_RATE) * num_losing_infectiousness  # most people recover
            num_deaths_today = DEATH_RATE * num_losing_infectiousness             # but some die
            
        if t >= MIN_DAYS_IMMUNE:
            # then some people might lose immunity today
            num_lost_immunity_today = FRACTION_WHO_LOSE_IMMUNITY * num_recovered_today_arry[ t - MIN_DAYS_IMMUNE ]

        # UPDATE THE 4 QUANTITIES WE WILL PLOT
        num_susceptible = num_susceptible - num_infected_today + num_lost_immunity_today
        num_infectious  = num_infectious + num_infected_today - num_recovered_today - num_deaths_today
        num_immune      = num_immune + num_recovered_today - num_lost_immunity_today
        num_dead        = num_dead + num_deaths_today

        # enable infection to disappear
        if num_infectious < 1.0:
            num_infectious = 0

        # append the quantities updated above into the time histories
        num_susceptible_arry.append( num_susceptible )        
        num_infected_today_arry.append( num_infected_today )
        num_recovered_today_arry.append( num_recovered_today )
        num_infectious_arry.append( num_infectious )
        num_immune_arry.append( num_immune )
        num_dead_arry.append( num_dead )

        # PRINT SOME STUFF

        if t == 0 or t == 1 or t > NUM_DAYS_SIMULATED-4:
            print(f'Day {t+1:4}: S={num_susceptible:.2f}  I={num_infectious:.2f}  R={num_immune:.2f}  D={num_dead:.2f}')
        
        if t_10_deaths == None and num_dead >= 10:
            t_10_deaths = t

        if t_10_deaths != None and (t - t_10_deaths) == 202:
            # US saw 200,000 deaths 200 days after seeing 10 deaths
            print(f'Day {t+1:4}: 202 days since 10 deaths: US had 200,000 deaths.  Sim has {num_dead:.0f}.')

        # sanity check: total people count should stay constant
        people_count = num_susceptible + num_infectious + num_immune + num_dead   # should stay constant
        people_count_error = abs(people_count - TOTAL_POPULATION)
        if people_count_error >= 1:
            print(f'ERROR: People count started at {TOTAL_POPULATION} but is now {people_count}')
            exit()

        #if t > NUM_DAYS_SIMULATED-4:
        #    print(f'Day {t+1:4}:  No. dead = {num_dead:.0f}  No. susceptible = {num_susceptible:.0f}.')
        
        #if t == NUM_DAYS_SIMULATED-1:
        #    print(f'Day {t+1:4}:  Final no. dead = {num_dead:.0f}.\n')

    # store the latest scenario

    num_susceptible_arry_arry.append(num_susceptible_arry)
    num_infectious_arry_arry.append(num_infectious_arry)
    num_immune_arry_arry.append(num_immune_arry)
    num_dead_arry_arry.append(num_dead_arry)

# PLOT RESULTS

fig, axs = plt.subplots(2, 2)

hday0 = str(herd_immunity_day[0])
nd0 = str(int(total_dead[0]))
hday1 = str(herd_immunity_day[1])
nd1 = str(int(total_dead[1]))

fig.suptitle('Simple Pandemic Simulation by Stan Mohler, Jr.\nMild social distancing: Infection gone in '
              + hday0 + ' days, ' + nd0 + ' dead\nNo social distancing: Infection gone in '
              + hday1 + ' days, ' + nd1 + ' dead', fontsize=8)

axs[0, 0].set_title('Susceptable')
axs[0, 1].set_title('Infected (Infectious)')
axs[1, 0].set_title('Recovered (Immune)')
axs[1, 1].set_title('Deaths')

x = range(NUM_DAYS_SIMULATED + 1)

for s in range(2):

    linestyle = '-'
    label = 'R0 = ' + str(LOW_INITIAL_REPRODUCTION_NUMBER)

    if s==1:
        linestyle = ':'
        label = 'R0 = ' + str(HIGH_INITIAL_REPRODUCTION_NUMBER)

    # For log plot, uncomment block below, comment out later axs[0,1] call.  Also, add "log()" to ylabel below
    #y = np.log(num_infectious_arry_arry[0])
    #axs[0,1].plot(x, y, 'tab:orange', linestyle=linestyle, label=label)

    axs[0,0].plot(x, num_susceptible_arry_arry[s], 'tab:blue', linestyle=linestyle, label=label)
    axs[0,1].plot(x, num_infectious_arry_arry[s], 'tab:orange', linestyle=linestyle, label=label)
    axs[1,0].plot(x, num_immune_arry_arry[s], 'tab:green', linestyle=linestyle, label=label)
    axs[1,1].plot(x, num_dead_arry_arry[s], 'tab:red', linestyle=linestyle, label=label)

    axs[0,0].legend(bbox_to_anchor=(0.98, 0.93), loc='upper right', borderaxespad=0.02, fontsize='xx-small')
    axs[0,1].legend(bbox_to_anchor=(0.98, 0.93), loc='upper right', borderaxespad=0.02, fontsize='xx-small')
    axs[1,0].legend(bbox_to_anchor=(0.98, 0.08), loc='lower right', borderaxespad=0.02, fontsize='xx-small')
    axs[1,1].legend(bbox_to_anchor=(0.98, 0.08), loc='lower right', borderaxespad=0.02, fontsize='xx-small')

for ax in axs.flat:
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    ax.set(xlabel='days', ylabel='no. people')

plt.subplots_adjust(left=0.2, bottom=None, right=None, top=0.83, wspace=0.9, hspace=0.5)

axs[0,1].annotate('infection gone', xy=(herd_immunity_day[0], 0), xytext=(herd_immunity_day[0]-690, 50e6),
             arrowprops=dict(facecolor='black', shrink=0.05),
             )

plt.show()
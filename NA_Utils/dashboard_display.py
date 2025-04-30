import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Sample patient data (replace with real-time updates)
vital_signs = {
    "John Doe": {"heart_rate": [], "spo2": [], "temperature": []},
    "Jane Smith": {"heart_rate": [], "spo2": [], "temperature": []},
}

risk_levels = {
    "John Doe": {"heart_rate": "green", "spo2": "green", "temperature": "green"},
    "Jane Smith": {"heart_rate": "green", "spo2": "green", "temperature": "green"},
}


def update_vital_signs(patient_name, heart_rate, spo2, temperature):
    vital_signs[patient_name]["heart_rate"].append(heart_rate)
    vital_signs[patient_name]["spo2"].append(spo2)
    vital_signs[patient_name]["temperature"].append(temperature)

    # Limit the number of data points to keep the plot readable
    for key in vital_signs[patient_name]:
        vital_signs[patient_name][key] = vital_signs[patient_name][key][-50:]

def update_risk_levels(patient_name, hr_risk, spo2_risk, temp_risk):
    risk_levels[patient_name]["heart_rate"] = hr_risk
    risk_levels[patient_name]["spo2"] = spo2_risk
    risk_levels[patient_name]["temperature"] = temp_risk

def display_dashboard(patients):
    fig, axes = plt.subplots(len(patients), 3, figsize=(15, 5 * len(patients)))
    fig.suptitle("Hospital Dashboard", fontsize=16)
    axes = axes.flatten()

    def animate(i):
        ax_index = 0  # Index for subplots
        for patient_name in patients:
            # Vitals data
            hr_data = vital_signs[patient_name]["heart_rate"]
            spo2_data = vital_signs[patient_name]["spo2"]
            temp_data = vital_signs[patient_name]["temperature"]

            # Heart Rate subplot
            axes[ax_index].clear()
            axes[ax_index].plot(hr_data, label="Heart Rate")
            axes[ax_index].set_title(f"{patient_name} - Heart Rate", color=risk_levels[patient_name]["heart_rate"])
            axes[ax_index].set_ylim(40, 140)  # Adjust limits as needed
            axes[ax_index].set_ylabel("BPM")
            axes[ax_index].legend(loc="upper left")
            ax_index += 1

            # SpO2 subplot
            axes[ax_index].clear()
            axes[ax_index].plot(spo2_data, label="SpO2", color="purple")
            axes[ax_index].set_title(f"{patient_name} - SpO2", color=risk_levels[patient_name]["spo2"])
            axes[ax_index].set_ylim(85, 105)  # Adjust limits as needed
            axes[ax_index].set_ylabel("%")
            axes[ax_index].legend(loc="upper left")
            ax_index += 1

            # Temperature subplot
            axes[ax_index].clear()
            axes[ax_index].plot(temp_data, label="Temperature", color="orange")
            axes[ax_index].set_title(f"{patient_name} - Temperature", color=risk_levels[patient_name]["temperature"])
            axes[ax_index].set_ylim(95, 105)  # Adjust limits as needed
            axes[ax_index].set_ylabel("°F")
            axes[ax_index].legend(loc="upper left")
            ax_index += 1

        fig.tight_layout()  # Adjust layout
        fig.subplots_adjust(top=0.90)  # Make space for the suptitle

    

    ani = animation.FuncAnimation(fig, animate, interval=1000)  # Update every 1 second
    plt.show()
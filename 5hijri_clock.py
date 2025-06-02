import tkinter as tk
from tkinter import ttk
import math
from datetime import datetime, timedelta
import threading
import time

class HijriAnalogClock:
    def __init__(self, root, latitude=33.6844, longitude=73.0479):
        self.root = root
        self.latitude = latitude
        self.longitude = longitude
        
        # Prayer configurations
        self.prayer_config = {
            'maghrib_to_isha': {'subdivisions': 3, 'color': '#8B4CB8', 'name': 'Evening'},
            'isha_to_fajr': {'subdivisions': 8, 'color': '#1E3A8A', 'name': 'Night'},
            'fajr_to_sunrise': {'subdivisions': 3, 'color': '#87CEEB', 'name': 'Dawn'},
            'sunrise_to_dhuhr': {'subdivisions': 6, 'color': '#FFD700', 'name': 'Morning'},
            'dhuhr_to_asr': {'subdivisions': 4, 'color': '#FF8C00', 'name': 'Midday'},
            'asr_to_maghrib': {'subdivisions': 5, 'color': '#DC143C', 'name': 'Afternoon'}
        }
        
        # Clock dimensions
        self.canvas_size = 500
        self.center_x = self.canvas_size // 2
        self.center_y = self.canvas_size // 2
        self.clock_radius = 200
        
        self.setup_ui()
        self.prayer_times = self.calculate_prayer_times(datetime.now())
        self.draw_clock_face()
        self.start_clock_update()
        
    def setup_ui(self):
        """Setup the Tkinter UI"""
        self.root.title("Hijri Analogue Clock")
        self.root.geometry("600x650")
        self.root.configure(bg='#f0f0f0')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        self.title_label = ttk.Label(main_frame, text="Hijri Analogue Clock (Resets at Sunrise)", 
                                    font=('Arial', 16, 'bold'))
        self.title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Canvas for clock
        self.canvas = tk.Canvas(main_frame, width=self.canvas_size, height=self.canvas_size, 
                               bg='white', highlightthickness=2, highlightbackground='#333')
        self.canvas.grid(row=1, column=0, pady=(0, 10))
        
        # Info frame
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Current time display
        self.time_label = ttk.Label(info_frame, text="", font=('Arial', 14, 'bold'))
        self.time_label.grid(row=0, column=0, pady=5)
        
        # Current period display
        self.period_label = ttk.Label(info_frame, text="", font=('Arial', 12))
        self.period_label.grid(row=1, column=0, pady=5)
        
        # Location input
        location_frame = ttk.Frame(info_frame)
        location_frame.grid(row=2, column=0, pady=10)
        
        ttk.Label(location_frame, text="Latitude:").grid(row=0, column=0, padx=5)
        self.lat_entry = ttk.Entry(location_frame, width=10)
        self.lat_entry.insert(0, str(self.latitude))
        self.lat_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(location_frame, text="Longitude:").grid(row=0, column=2, padx=5)
        self.lng_entry = ttk.Entry(location_frame, width=10)
        self.lng_entry.insert(0, str(self.longitude))
        self.lng_entry.grid(row=0, column=3, padx=5)
        
        ttk.Button(location_frame, text="Update Location", 
                  command=self.update_location).grid(row=0, column=4, padx=10)
    
    def update_location(self):
        """Update location and recalculate prayer times"""
        try:
            self.latitude = float(self.lat_entry.get())
            self.longitude = float(self.lng_entry.get())
            self.prayer_times = self.calculate_prayer_times(datetime.now())
            self.draw_clock_face()
        except ValueError:
            pass  # Invalid input, ignore
    
    def calculate_prayer_times(self, date):
        """Simplified prayer time calculation"""
        base_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Approximate prayer times (replace with accurate calculations)
        prayer_times = {
            'maghrib': base_date.replace(hour=18, minute=30),
            'isha': base_date.replace(hour=20, minute=0),
            'fajr': base_date.replace(hour=5, minute=0),
            'sunrise': base_date.replace(hour=6, minute=30),
            'dhuhr': base_date.replace(hour=12, minute=30),
            'asr': base_date.replace(hour=15, minute=30)
        }
        
        return prayer_times
    
    def time_to_angle(self, time):
        """Convert time to angle on the Hijri clock (0° at Sunrise, clockwise - resets at sunrise)"""
        sunrise = self.prayer_times['sunrise']
        
        # Calculate hours since sunrise (this is where the day resets)
        if time >= sunrise:
            hours_since_sunrise = (time - sunrise).total_seconds() / 3600
        else:
            # Before sunrise - calculate from previous day's sunrise
            previous_sunrise = sunrise - timedelta(days=1)
            hours_since_sunrise = (time - previous_sunrise).total_seconds() / 3600
        
        # Reset every 24 hours (full rotation) - this is where the "12:00 reset" equivalent happens
        hours_since_sunrise = hours_since_sunrise % 24
        
        # Convert to angle (24 hours = 360°, starting from West/180° where sunrise is)
        angle = (hours_since_sunrise / 24) * 360 + 180  # +180 to start at West
        return angle % 360
    
    def polar_to_cartesian(self, angle_deg, radius):
        """Convert polar coordinates to cartesian for canvas"""
        # Adjust angle: Tkinter 0° is East, but we want Maghrib at East
        angle_rad = math.radians(angle_deg)
        x = self.center_x + radius * math.cos(angle_rad)
        y = self.center_y + radius * math.sin(angle_rad)
        return x, y
    
    def draw_clock_face(self):
        """Draw the static elements of the clock face"""
        self.canvas.delete("all")
        
        # Draw outer circle
        self.canvas.create_oval(self.center_x - self.clock_radius, 
                               self.center_y - self.clock_radius,
                               self.center_x + self.clock_radius, 
                               self.center_y + self.clock_radius,
                               outline='black', width=3)
        
        # Draw prayer period arcs and subdivisions
        self.draw_prayer_periods()
        
        # Draw main diameter (Sunrise-Maghrib line - Sunrise is now the reset point)
        sunrise_x, sunrise_y = self.polar_to_cartesian(180, self.clock_radius - 10)
        maghrib_x, maghrib_y = self.polar_to_cartesian(0, self.clock_radius - 10)
        self.canvas.create_line(sunrise_x, sunrise_y, maghrib_x, maghrib_y, 
                               fill='black', width=3)
        
        # Draw prayer time markers
        self.draw_prayer_markers()
        
        # Draw center dot
        self.canvas.create_oval(self.center_x - 5, self.center_y - 5,
                               self.center_x + 5, self.center_y + 5,
                               fill='black', outline='black')
        
        # Add labels
        self.add_labels()
    
    def draw_prayer_periods(self):
        """Draw colored arcs for each prayer period with subdivisions"""
        prayer_order = ['maghrib', 'isha', 'fajr', 'sunrise', 'dhuhr', 'asr']
        period_names = ['maghrib_to_isha', 'isha_to_fajr', 'fajr_to_sunrise', 
                       'sunrise_to_dhuhr', 'dhuhr_to_asr', 'asr_to_maghrib']
        
        for i, period_name in enumerate(period_names):
            start_prayer = prayer_order[i]
            end_prayer = prayer_order[(i + 1) % len(prayer_order)]
            
            start_angle = self.time_to_angle(self.prayer_times[start_prayer])
            end_angle = self.time_to_angle(self.prayer_times[end_prayer])
            
            # Handle angle wraparound
            if end_angle < start_angle:
                end_angle += 360
            
            config = self.prayer_config[period_name]
            num_subdivisions = config['subdivisions']
            color = config['color']
            
            # Draw subdivisions
            angle_step = (end_angle - start_angle) / num_subdivisions
            
            for j in range(num_subdivisions):
                sub_start = start_angle + j * angle_step
                sub_end = start_angle + (j + 1) * angle_step
                
                # Draw arc segment
                radius_inner = self.clock_radius - 40
                radius_outer = self.clock_radius - 15 - (j % 2) * 5
                
                self.draw_arc_segment(sub_start, sub_end, radius_inner, radius_outer, color)
                
                # Draw subdivision tick marks
                if j > 0:
                    tick_x1, tick_y1 = self.polar_to_cartesian(sub_start, radius_inner)
                    tick_x2, tick_y2 = self.polar_to_cartesian(sub_start, radius_outer)
                    self.canvas.create_line(tick_x1, tick_y1, tick_x2, tick_y2, 
                                           fill=color, width=1)
    
    def draw_arc_segment(self, start_angle, end_angle, radius_inner, radius_outer, color):
        """Draw an arc segment between two radii"""
        # Create polygon points for the arc segment
        points = []
        
        # Inner arc points
        for angle in range(int(start_angle), int(end_angle) + 1, 2):
            x, y = self.polar_to_cartesian(angle, radius_inner)
            points.extend([x, y])
        
        # Outer arc points (reverse order)
        for angle in range(int(end_angle), int(start_angle) - 1, -2):
            x, y = self.polar_to_cartesian(angle, radius_outer)
            points.extend([x, y])
        
        if len(points) >= 6:  # Need at least 3 points
            self.canvas.create_polygon(points, fill=color, outline=color, width=1)
    
    def draw_prayer_markers(self):
        """Draw prayer time markers"""
        for prayer, time in self.prayer_times.items():
            angle = self.time_to_angle(time)
            
            # Draw tick mark
            tick_x1, tick_y1 = self.polar_to_cartesian(angle, self.clock_radius - 15)
            tick_x2, tick_y2 = self.polar_to_cartesian(angle, self.clock_radius + 5)
            self.canvas.create_line(tick_x1, tick_y1, tick_x2, tick_y2, 
                                   fill='blue', width=3)
            
            # Add prayer name
            label_x, label_y = self.polar_to_cartesian(angle, self.clock_radius + 25)
            self.canvas.create_text(label_x, label_y, text=prayer.capitalize(),
                                   fill='blue', font=('Arial', 9, 'bold'))
    
    def add_labels(self):
        """Add main labels to the clock"""
        # Sunrise (West/180° - This is now the reset point, like 12:00 on regular clock)
        sunrise_x, sunrise_y = self.polar_to_cartesian(180, self.clock_radius + 40)
        # self.canvas.create_text(sunrise_x, sunrise_y, text="Sunrise\n(Reset Point)",
        #                        fill='darkorange', font=('Arial', 11, 'bold'))
        
        # # Maghrib (East/0°)
        # maghrib_x, maghrib_y = self.polar_to_cartesian(0, self.clock_radius + 40)
        # self.canvas.create_text(maghrib_x, maghrib_y, text="Maghrib\n(Sunset)",
        #                        fill='darkorange', font=('Arial', 11, 'bold'))
        
        # Solar Noon (North/270°)
        noon_x, noon_y = self.polar_to_cartesian(270, self.clock_radius + 30)
        # self.canvas.create_text(noon_x, noon_y, text="Solar Noon",
        #                        fill='red', font=('Arial', 10))
    
    def draw_clock_hands(self):
        """Draw the clock hands"""
        # Clear previous hands
        self.canvas.delete("hand")
        
        current_time = datetime.now()
        
        # Calculate angles for hands
        main_angle = self.time_to_angle(current_time)
        
        # Main hand (shows current time in Hijri day)
        main_x, main_y = self.polar_to_cartesian(main_angle, self.clock_radius - 50)
        self.canvas.create_line(self.center_x, self.center_y, main_x, main_y,
                               fill='black', width=4, tags="hand")
        self.canvas.create_oval(main_x - 4, main_y - 4, main_x + 4, main_y + 4,
                               fill='red', outline='red', tags="hand")
        
        # Minute hand (shows minutes within current hour)
        minute_angle = main_angle + (current_time.minute / 60) * 15  # 15° per hour
        minute_x, minute_y = self.polar_to_cartesian(minute_angle, self.clock_radius - 80)
        self.canvas.create_line(self.center_x, self.center_y, minute_x, minute_y,
                               fill='blue', width=3, tags="hand")
        
        # Second hand (shows seconds within current minute)
        second_angle = minute_angle + (current_time.second / 60) * 0.25  # 0.25° per minute
        second_x, second_y = self.polar_to_cartesian(second_angle, self.clock_radius - 60)
        self.canvas.create_line(self.center_x, self.center_y, second_x, second_y,
                               fill='red', width=1, tags="hand")
        self.canvas.create_oval(second_x - 2, second_y - 2, second_x + 2, second_y + 2,
                               fill='red', outline='red', tags="hand")
        
        # Center dot (on top of hands)
        self.canvas.create_oval(self.center_x - 6, self.center_y - 6,
                               self.center_x + 6, self.center_y + 6,
                               fill='black', outline='black', tags="hand")
    
    def get_current_period(self):
        """Get current prayer period"""
        current_time = datetime.now()
        hour = current_time.hour
        
        if 18 <= hour < 20:
            return 'maghrib_to_isha'
        elif 20 <= hour or hour < 5:
            return 'isha_to_fajr'
        elif 5 <= hour < 6.5:
            return 'fajr_to_sunrise'
        elif 6.5 <= hour < 12.5:
            return 'sunrise_to_dhuhr'
        elif 12.5 <= hour < 15.5:
            return 'dhuhr_to_asr'
        else:
            return 'asr_to_maghrib'
    
    def update_clock(self):
        """Update clock hands and display information"""
        while True:
            try:
                current_time = datetime.now()
                
                # Update hands
                self.root.after(0, self.draw_clock_hands)
                
                # Update time display with reset information
                current_time = datetime.now()
                sunrise_time = self.prayer_times['sunrise']
                
                # Calculate hours since last sunrise reset
                if current_time >= sunrise_time:
                    hours_since_reset = (current_time - sunrise_time).total_seconds() / 3600
                else:
                    previous_sunrise = sunrise_time - timedelta(days=1)
                    hours_since_reset = (current_time - previous_sunrise).total_seconds() / 3600
                
                hours_since_reset = hours_since_reset % 24
                
                time_str = current_time.strftime("%H:%M:%S")
                reset_str = f"Hours since sunrise reset: {hours_since_reset:.2f}"
                self.root.after(0, lambda: self.time_label.config(
                    text=f"Current Time: {time_str}\n{reset_str}"))
                
                # Update period display
                current_period = self.get_current_period()
                period_name = self.prayer_config[current_period]['name']
                self.root.after(0, lambda: self.period_label.config(
                    text=f"Current Period: {period_name}"))
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                break
    
    def start_clock_update(self):
        """Start the clock update thread"""
        self.update_thread = threading.Thread(target=self.update_clock, daemon=True)
        self.update_thread.start()

def main():
    root = tk.Tk()
    app = HijriAnalogClock(root)
    root.mainloop()

if __name__ == "__main__":
    main()
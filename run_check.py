import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import cv2
from PIL import Image, ImageTk

class GymApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gym App - Coach")
        self.root.geometry("900x600")
        self.json_file = "gym_database.json"
        self.load_json()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Client Management")
        self.setup_tab1()

        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Exercise Management")
        self.setup_tab2()

    def load_json(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = []
            self.save_json()

    def save_json(self):
        with open(self.json_file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def setup_tab1(self):
        # Left: form; Right: client list
        form_frame = ttk.Frame(self.tab1, padding=10)
        form_frame.pack(side='left', fill='y')

        ttk.Label(form_frame, text="Client ID:").grid(row=0, column=0, sticky='w', pady=5)
        self.entry_client_id = ttk.Entry(form_frame, width=25)
        self.entry_client_id.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(form_frame, text="Username:").grid(row=1, column=0, sticky='w', pady=5)
        self.entry_username = ttk.Entry(form_frame, width=25)
        self.entry_username.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky='w', pady=5)
        self.entry_password = ttk.Entry(form_frame, width=25, show="*")
        self.entry_password.grid(row=2, column=1, pady=5, padx=5)

        ttk.Button(form_frame, text="Add Client", command=self.add_client).grid(row=3, column=0, columnspan=2, pady=10, sticky='ew')

        # Right side: client list with scrollbar
        list_frame = ttk.Frame(self.tab1, padding=10)
        list_frame.pack(side='right', fill='both', expand=True)

        ttk.Label(list_frame, text="Select Client:").pack(anchor='nw')
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill='both', expand=True, pady=5)

        self.client_listbox = tk.Listbox(listbox_frame, exportselection=False)
        self.client_listbox.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.client_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.client_listbox.config(yscrollcommand=scrollbar.set)

        self.client_listbox.bind('<<ListboxSelect>>', self.select_client)
        self.update_client_list()

    def add_client(self):
        client_id = self.entry_client_id.get().strip()
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        if not (client_id and username and password):
            messagebox.showerror("Error", "Please enter all fields.")
            return
        if any(c['client_id'] == client_id for c in self.data):
            messagebox.showerror("Error", "Client ID already exists.")
            return
        self.data.append({
            "client_id": client_id,
            "username": username,
            "password": password,
            "exercises": []
        })
        self.save_json()
        self.update_client_list()
        messagebox.showinfo("Success", f"Added client {client_id}")
        # clear fields
        self.entry_client_id.delete(0, tk.END)
        self.entry_username.delete(0, tk.END)
        self.entry_password.delete(0, tk.END)

    def update_client_list(self):
        self.client_listbox.delete(0, tk.END)
        for client in self.data:
            self.client_listbox.insert(tk.END, client['client_id'])

    def select_client(self, event):
        selection = self.client_listbox.curselection()
        if selection:
            self.current_client_id = self.client_listbox.get(selection[0])
            self.notebook.select(self.tab2)
            self.update_tab2()

    def setup_tab2(self):
        self.exercise_frame = ttk.Frame(self.tab2, padding=10)
        self.exercise_frame.pack(fill='both', expand=True)

    def update_tab2(self):
        for widget in self.exercise_frame.winfo_children():
            widget.destroy()

        client = next((c for c in self.data if c['client_id'] == getattr(self, 'current_client_id', None)), None)
        if client is None:
            ttk.Label(self.exercise_frame, text="No client selected.").pack(pady=10)
            return

        header = ttk.Label(self.exercise_frame, text=f"Exercises for {self.current_client_id}", font=('Segoe UI', 12, 'bold'))
        header.pack(anchor='nw', pady=5)

        # listbox with scrollbar (kept for compatibility)
        list_frame = ttk.Frame(self.exercise_frame)
        list_frame.pack(fill='both', expand=True)

        self.exercise_listbox = tk.Listbox(list_frame, exportselection=False)
        self.exercise_listbox.pack(side='left', fill='both', expand=True, padx=(0,5))
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.exercise_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.exercise_listbox.config(yscrollcommand=scrollbar.set)

        for ex in client['exercises']:
            self.exercise_listbox.insert(tk.END, ex['name'])
        self.exercise_listbox.bind('<<ListboxSelect>>', self.select_exercise)

        # toolbar with buttons
        toolbar = ttk.Frame(self.exercise_frame)
        toolbar.pack(fill='x', pady=8)
        ttk.Button(toolbar, text="Add Exercise", command=self.add_exercise).pack(side='left', padx=4)
        ttk.Button(toolbar, text="Edit Exercise", command=self.edit_exercise).pack(side='left', padx=4)
        ttk.Button(toolbar, text="Move Up", command=lambda: self.move_exercise(-1)).pack(side='left', padx=4)
        ttk.Button(toolbar, text="Move Down", command=lambda: self.move_exercise(1)).pack(side='left', padx=4)
        ttk.Button(toolbar, text="Refresh", command=self.update_tab2).pack(side='right', padx=4)

    def select_exercise(self, event):
        if not hasattr(self, 'exercise_listbox'):
            return
        sel = self.exercise_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        client = next((c for c in self.data if c['client_id'] == getattr(self, 'current_client_id', None)), None)
        if client is None:
            return
        exercise = client['exercises'][index]
        info = (
            f"Name: {exercise.get('name')}\n"
            f"Angle Threshold: {exercise.get('thresholds', {}).get('angle_threshold')}\n"
            f"Distance Threshold: {exercise.get('thresholds', {}).get('distance_threshold')}\n"
            f"Target Reps: {exercise.get('target_reps')}\n"
            f"Rest Time: {exercise.get('rest_time')}s"
        )
        if exercise.get('video_path'):
            if messagebox.askyesno("Play Video", info + "\n\nPlay instruction video?"):
                self.play_video(exercise['video_path'])
        else:
            messagebox.showinfo("Exercise", info)

    def play_video(self, path):
        if not path:
            messagebox.showerror("Error", "No video to play.")
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", f"Video file not found: {path}")
            return
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            messagebox.showerror("Error", f"Cannot open video: {path}")
            return
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow('Video', frame)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def add_exercise(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Exercise")
        dialog.geometry("420x460")

        ttk.Label(dialog, text="Exercise Name:").pack(pady=5)
        entry_name = ttk.Entry(dialog)
        entry_name.pack(pady=5, fill='x', padx=10)

        ttk.Label(dialog, text="Angle Threshold:").pack(pady=5)
        entry_angle = ttk.Entry(dialog)
        entry_angle.pack(pady=5, fill='x', padx=10)
        entry_angle.insert(0, "90")

        ttk.Label(dialog, text="Distance Threshold:").pack(pady=5)
        entry_dist = ttk.Entry(dialog)
        entry_dist.pack(pady=5, fill='x', padx=10)
        entry_dist.insert(0, "30")

        ttk.Label(dialog, text="Target Reps:").pack(pady=5)
        entry_reps = ttk.Entry(dialog)
        entry_reps.pack(pady=5, fill='x', padx=10)
        entry_reps.insert(0, "10")

        ttk.Label(dialog, text="Rest Time (s):").pack(pady=5)
        entry_rest = ttk.Entry(dialog)
        entry_rest.pack(pady=5, fill='x', padx=10)
        entry_rest.insert(0, "60")

        ttk.Label(dialog, text="Video (optional):").pack(pady=5)
        video_path_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=video_path_var, state='readonly').pack(pady=5, fill='x', padx=10)
        ttk.Button(dialog, text="Choose/Record Video", command=lambda: video_path_var.set(self.record_or_select_video())).pack(pady=5)

        def try_save():
            try:
                angle = float(entry_angle.get())
                dist = float(entry_dist.get())
                reps = int(entry_reps.get())
                rest = int(entry_rest.get())
            except Exception:
                messagebox.showerror("Error", "Please enter valid numeric values.")
                return
            self.save_exercise(dialog, {
                "name": entry_name.get().strip(),
                "thresholds": {
                    "angle_threshold": angle,
                    "distance_threshold": dist
                },
                "target_reps": reps,
                "rest_time": rest,
                "video_path": video_path_var.get()
            })

        ttk.Button(dialog, text="Save", command=try_save).pack(pady=10)

    def record_or_select_video(self):
        choice = messagebox.askquestion("Video", "Record a new video or choose an existing file?\nYes = Record, No = Choose file")
        if choice == 'yes':
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showerror("Error", "Cannot access the camera.")
                return ""
            video_path = f"videos/{self.current_client_id}_{os.urandom(4).hex()}.mp4"
            os.makedirs("videos", exist_ok=True)
            out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (640, 480))
            recording = True
            while recording:
                ret, frame = cap.read()
                if ret:
                    out.write(frame)
                    cv2.imshow('Recording Video (press q to stop)', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        recording = False
                else:
                    break
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            return video_path
        else:
            return filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi")])

    def save_exercise(self, dialog, exercise):
        if not exercise['name']:
            messagebox.showerror("Error", "Exercise name cannot be empty.")
            return
        client = next((c for c in self.data if c['client_id'] == getattr(self, 'current_client_id', None)), None)
        if client is None:
            messagebox.showerror("Error", "No client selected.")
            return
        if any(ex['name'] == exercise['name'] for ex in client['exercises']):
            messagebox.showerror("Error", "Exercise name already exists.")
            return
        client['exercises'].append(exercise)
        self.save_json()
        self.update_tab2()
        dialog.destroy()
        messagebox.showinfo("Success", f"Added {exercise['name']}")

    def edit_exercise(self):
        selection = self.exercise_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an exercise.")
            return
        exercise_name = self.exercise_listbox.get(selection[0])
        client = next((c for c in self.data if c['client_id'] == getattr(self, 'current_client_id', None)), None)
        if client is None:
            messagebox.showerror("Error", "No client selected.")
            return
        exercise = next(ex for ex in client['exercises'] if ex['name'] == exercise_name)

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Exercise")
        dialog.geometry("420x460")

        ttk.Label(dialog, text="Exercise Name:").pack(pady=5)
        entry_name = ttk.Entry(dialog)
        entry_name.pack(pady=5, fill='x', padx=10)
        entry_name.insert(0, exercise['name'])
        entry_name.config(state='disabled')

        ttk.Label(dialog, text="Angle Threshold:").pack(pady=5)
        entry_angle = ttk.Entry(dialog)
        entry_angle.pack(pady=5, fill='x', padx=10)
        entry_angle.insert(0, exercise['thresholds']['angle_threshold'])

        ttk.Label(dialog, text="Distance Threshold:").pack(pady=5)
        entry_dist = ttk.Entry(dialog)
        entry_dist.pack(pady=5, fill='x', padx=10)
        entry_dist.insert(0, exercise['thresholds']['distance_threshold'])

        ttk.Label(dialog, text="Target Reps:").pack(pady=5)
        entry_reps = ttk.Entry(dialog)
        entry_reps.pack(pady=5, fill='x', padx=10)
        entry_reps.insert(0, exercise['target_reps'])

        ttk.Label(dialog, text="Rest Time (s):").pack(pady=5)
        entry_rest = ttk.Entry(dialog)
        entry_rest.pack(pady=5, fill='x', padx=10)
        entry_rest.insert(0, exercise['rest_time'])

        ttk.Label(dialog, text="Video (optional):").pack(pady=5)
        video_path_var = tk.StringVar(value=exercise.get('video_path', ''))
        ttk.Entry(dialog, textvariable=video_path_var, state='readonly').pack(pady=5, fill='x', padx=10)
        ttk.Button(dialog, text="Choose/Record Video", command=lambda: video_path_var.set(self.record_or_select_video())).pack(pady=5)

        def try_save_edit():
            try:
                angle = float(entry_angle.get())
                dist = float(entry_dist.get())
                reps = int(entry_reps.get())
                rest = int(entry_rest.get())
            except Exception:
                messagebox.showerror("Error", "Please enter valid numeric values.")
                return
            self.save_edited_exercise(dialog, exercise, {
                "angle_threshold": angle,
                "distance_threshold": dist,
                "target_reps": reps,
                "rest_time": rest,
                "video_path": video_path_var.get()
            })

        ttk.Button(dialog, text="Save", command=try_save_edit).pack(pady=10)

    def save_edited_exercise(self, dialog, old_exercise, updates):
        client = next((c for c in self.data if c['client_id'] == getattr(self, 'current_client_id', None)), None)
        if client is None:
            messagebox.showerror("Error", "No client selected.")
            return
        index = client['exercises'].index(old_exercise)
        client['exercises'][index].update({
            "thresholds": {
                "angle_threshold": updates['angle_threshold'],
                "distance_threshold": updates['distance_threshold']
            },
            "target_reps": updates['target_reps'],
            "rest_time": updates['rest_time'],
            "video_path": updates['video_path']
        })
        self.save_json()
        self.update_tab2()
        dialog.destroy()
        messagebox.showinfo("Success", f"Updated {old_exercise['name']}")

    def move_exercise(self, direction):
        selection = self.exercise_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an exercise.")
            return
        index = selection[0]
        client = next((c for c in self.data if c['client_id'] == getattr(self, 'current_client_id', None)), None)
        if client is None:
            messagebox.showerror("Error", "No client selected.")
            return
        if (direction == -1 and index > 0) or (direction == 1 and index < len(client['exercises']) - 1):
            client['exercises'][index], client['exercises'][index + direction] = \
                client['exercises'][index + direction], client['exercises'][index]
            self.save_json()
            self.update_tab2()
            # re-select moved item
            self.exercise_listbox.selection_set(index + direction)

if __name__ == "__main__":
    root = tk.Tk()
    app = GymApp(root)
    root.mainloop()

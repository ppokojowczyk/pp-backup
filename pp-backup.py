#!/usr/bin/env python3
from tkinter import filedialog
import datetime
import tarfile
import tkinter as tk
import tkinter.ttk as ttk
import json
import os
import tkinter.font as TkFont
from shutil import copyfile
from pathlib import Path

class ppBudget(tk.Frame):

    def __init__(self, master=None):
        self.initializeFont()
        self.bg = "#333"
        tk.Frame.__init__(self, master, padx=5, pady=5, width=800, height=575, bg=self.bg, relief=tk.SUNKEN)
        self.pack_propagate(0)
        self.pack(fill=tk.BOTH, expand=True)
        self.targetDir = ''
        self.widgets = {}
        self.createPresetsWidget()
        self.createTargetDirSelector()
        self.createLogBox()
        self.createButtons()
        self.processWidgets([
            self.getWidget('presets'),
            self.getWidget('targetDir'),
            self.getWidget('targetFilename'),
            self.getWidget('selectTargetDirButton'),
            self.getWidget('logBox')
        ])
        self.processButtons([
            self.getWidget('runButton'),
            self.getWidget('quitButton')
        ])
        self.addLog("Hi,\n\nSelect one of existing presets, set target directory and click Run button to create backup archive.\n")
        self.initPresets()
        self.populatePresetsWidget(self.presets)
        self.master.update_idletasks()

    """
    Initialize font.
    """
    def initializeFont(self):
        self.__font = TkFont.Font(family='monospace', size=9)

    """
    Initialize presets.
    """
    def initPresets(self):
        self.presets = []
        if os.path.exists("presets.json") == False and os.path.exists("presets.json.example"):
            self.addLog("(!) Copied example presets to new presets.json file.")
            copyfile("presets.json.example", "presets.json")
        if os.path.exists("presets.json"):
            json_string = open("presets.json", "r").read()
            loadedPresets = json.loads(json_string)
            for preset in loadedPresets:
                if(self.verifyPreset(preset)):
                    self.presets.append(preset)

    """
    Verify preset.
    """
    def verifyPreset(self, preset):
        return True if 'name' in preset and 'sources' in preset else False

    """
    Returns widget by its name.
    """
    def getWidget(self, name):
        return self.widgets[name]

    """
    Add log entry.
    """
    def addLog(self, text):
        w = self.getWidget('logBox')
        w.config(state='normal')
        w.insert(tk.END, text + "\n")
        w.config(state='disabled')
        w.see(tk.END)

    """
    Initialize directory selection widget.
    """
    def selectTargetDir(self):
        targetDir = filedialog.askdirectory()
        self.getWidget('targetDir').config(state='normal')
        self.getWidget('targetDir').delete(1.0,tk.END)
        self.getWidget('targetDir').insert(tk.END, targetDir or '')
        self.getWidget('targetDir').config(state='disabled')
        self.targetDir = targetDir or ''

    """
    Initialize target directory selector.
    """
    def createTargetDirSelector(self):
        f = tk.Frame(self, background=self.bg)
        f.pack(fill="both")

        w = tk.Text(f)
        w.config(wrap='none', height=1)
        w.delete(1.0,tk.END)

        self.targetDir = os.path.dirname(os.path.abspath(__file__)) + "/backups/"
        w.insert(tk.END, self.targetDir)

        w.config(state='disabled')
        w.pack(side=tk.LEFT, fill="both")
        self.widgets['targetDir'] = w

        b = tk.Button(f, text="Select target dir")
        b.configure(command=self.selectTargetDir)
        b.pack(side=tk.LEFT, fill="both")
        self.widgets['selectTargetDirButton'] = b;

    """
    Create buttons.
    """
    def createButtons(self):
        f = tk.Frame(self, background=self.bg)
        f.pack(anchor=tk.CENTER, padx=0)

        r = tk.Button(f, text="Run", bg="#0A0", fg="#FFF", bd=0,
            highlightbackground="#0E0", activebackground="#0F0", activeforeground="#FFF")
        r.configure(command=self.doBackup)
        r.pack(side=tk.LEFT)
        self.widgets['runButton'] = r

        q = tk.Button(f, text="Quit", bg="#A00", fg="#FFF", bd=0,
            highlightbackground="#E00", activebackground="#F00", activeforeground="#FFF")
        q.configure(command=self.quit)
        q.pack(side=tk.LEFT)
        self.widgets['quitButton'] = q

    """
    Execute when preset was selected.
    """
    def onPresetSelected(self, preset):
        preset = self.getPreset(self.widgets['presets'].get())
        if(False == preset):
            return
        self.setTargetFilename(self.createFilenameWithPrefix(preset["fileNamePrefix"]))

    """
    Create "presets" select widget.
    """
    def createPresetsWidget(self):
        s = ttk.Combobox(self)
        self.widgets['presets'] = s
        s.pack(fill="both")
        s.config(state='readonly')
        s.bind("<<ComboboxSelected>>", self.onPresetSelected)
        
        # "Target Filename" widget.
        w = tk.Text(self, height=0)
        date = datetime.datetime.now()
        w.insert(tk.END, "backup_" + date.strftime("%Y_%m_%d_%H_%M_%S") + '.tar.gz')
        w.pack(fill="both")
        self.widgets['targetFilename'] = w

    def populatePresetsWidget(self, presets):
        values = []
        for preset in self.presets:
            values.append(preset['name'])
        self.getWidget('presets').config(values=values)

    """
    Set target archive filename.
    """
    def setTargetFilename(self, filename):
        w = self.getWidget('targetFilename')
        w.delete("1.0", "end")
        w.insert(tk.END, filename)

    """
    Execute backup.
    """
    def doBackup(self):
        valid = True
        date = datetime.datetime.now()
        presetName = self.widgets['presets'].get()
        self.addLog("")
        self.addLog("--------------------")
        self.addLog(date.strftime("%Y_%m_%d_%H_%M_%S"))
        self.addLog("")

        if(self.targetDir == ''):
            self.addLog('No target directory selected.')
            valid = False

        if(presetName == ''):
            self.addLog('No preset selected.')
            valid = False

        preset = self.getPreset(presetName)
        if(self.verify(preset) != True):
            valid = False

        if(False == valid):
            self.addLog("\nFailed.")
            self.addLog("--------------------")
            return False

        filename = self.getFileName()
        if(filename == None or filename == False):
            self.addLog("Invalid filename.")
            return False

        filepath = self.getAbsoluteFilePath()
        if os.path.exists(filepath):
            self.addLog("(!) File already exists.")
            return False

        tar = tarfile.open(self.getAbsoluteFilePath(), "w:gz")
        self.addLog("Created archive " + filename)
        for f in preset['sources']:
            self.addLog("Adding " + f)
            tar.add(f, "")
            self.addLog("\t+ done")
        tar.close()
        self.addLog("Finished.")

    """
    Create filename with prefix
    """
    def createFilenameWithPrefix(self, prefix = ''):
        date = datetime.datetime.now()
        return (prefix + "__" if prefix else "") + "backup_" + date.strftime("%Y_%m_%d_%H_%M_%S") + '.tar.gz'

    """
    Get filename.
    """
    def getFileName(self):
        return self.getWidget('targetFilename').get("1.0", "end").rstrip()

    """
    Get absolute file path.
    """
    def getAbsoluteFilePath(self):
        return self.targetDir + '/' + self.getFileName()

    """
    Get preset.
    """
    def getPreset(self, name):
        for f in self.presets:
            if(f['name'] == name):
                return f
        return False

    """
    Create textbox.
    """
    def createLogBox(self):
        w = tk.Text(self, bg=self.bg, fg="#EFEFEF", padx=10, pady=10, highlightbackground="#888")
        w.config(font=self.__font)        
        w.pack(fill="both")
        w.config(state='disabled')
        self.widgets['logBox'] = w

    """
    Verify data before processing archive.
    """
    def verify(self, preset):
        valid = True
        for f in preset['sources']:
            filePath = Path(f)
            if filePath.exists() != True:
                self.addLog("Source doesn't exist: " + f)
                valid = False
        return valid

    """
    Apply styling to widgets.
    """
    def processWidgets(self, widgets):
        for widget in widgets:
            widget.pack(padx=5, pady=5)
    
    def processButtons(self, buttons):
        for button in buttons:
            button.config(height=50, width=49, border=1)
            button.pack(padx=5, pady=0)

mw = tk.Tk()
mw.geometry("800x550")
mw.resizable(0,0)
applicationInstance = ppBudget(mw)
applicationInstance.master.title('pp-backup')
applicationInstance.mainloop()

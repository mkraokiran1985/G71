#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
if globals().has_key('init_modules'):
    for m in [x for x in sys.modules.keys() if x not in init_modules]:
        del(sys.modules[m]) 
else:
    init_modules = sys.modules.keys()


import sys, os, string, ConfigParser
from dxf2gcode_v01_point import PointClass
from dxf2gcode_v01_shape import ShapeClass
import dxf2gcode_v01_dxf_import as dxf_import 
import dxf2gcode_v01_tsp_opt as tsp


import webbrowser
from Tkconstants import END, INSERT, ALL, N, S, E, W, RAISED, RIDGE, GROOVE, FLAT, DISABLED, NORMAL, ACTIVE, LEFT
from tkMessageBox import showwarning, showerror
from Tkinter import Tk, Canvas, Menu, Frame, Grid, DoubleVar, StringVar , IntVar, Radiobutton,Checkbutton, Label, Entry, Text, Scrollbar, Toplevel,Button , PhotoImage
from tkFileDialog import askopenfile, asksaveasfilename
from tkSimpleDialog import askfloat
from Canvas import Rectangle, Line, Oval, Arc
from copy import copy

from math import radians, cos, sin
import re
APPNAME = "dxf2gcode_v01"

class Erstelle_Fenster:
    def __init__(self, master = None, load_filename=None ):
        
        self.master=master     

        self.load_filename=load_filename

        self.frame_l=Frame(master) 
        self.frame_l.grid(row=0,column=0,rowspan=2,padx=4,pady=4,sticky=N+E+W)
        
        self.frame_c=Frame(master,relief = RIDGE,bd = 2)
        self.frame_c.grid(row=0,column=1,padx=4,pady=4,sticky=N+E+S+W)
        
        self.frame_u=Frame(master) 
        self.frame_u.grid(row=1,column=1,padx=4,sticky=N+E+W+S)
        self.textbox=TextboxClass(frame=self.frame_u,master=self.master)

        self.config=ConfigClass(self.textbox)

        self.postpro=PostprocessorClass(self.config,self.textbox)

        self.master.columnconfigure(0,weight=0)
        self.master.columnconfigure(1,weight=1)
        self.master.rowconfigure(0,weight=1)
        self.master.rowconfigure(1,weight=0)
            

        self.ExportParas =ExportParasClass(self.frame_l,self.config,self.postpro)
        self.Canvas =CanvasClass(self.frame_c,self)

        self.CanvasContent=CanvasContentClass(self.Canvas,self.textbox,self.config)
        self.Canvas.Content=self.CanvasContent

        self.erstelle_menu()        
        
        if not(self.load_filename==None):
            self.Canvas.canvas.update()
            self.Load_File(self.load_filename)
            
        self.b = Button(self.frame_u, text="Reverse",command=self.CanvasContent.switch_shape_dir)
        self.b.grid(row=1)
        self.bt1 = Button(self.frame_l, text="Added",command=self.Add_to_File)
        self.bt1.grid(row=3,column=1,sticky=W)
        self.bt2 = Button(self.frame_l, text="Write",command=self.Write_GCode)
        self.bt2.grid(row=3,column=1,sticky=E)
        
    def erstelle_menu(self): 
        self.menu = Menu(self.master)
        self.master.config(menu=self.menu)

        self.filemenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="Read DXF", command=self.Get_Load_File)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.ende)

        self.exportmenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="Export", menu=self.exportmenu)
        self.exportmenu.add_command(label="Write G-Code", command=self.Write_GCode)
        self.exportmenu.entryconfig(0,state=DISABLED)

        self.viewmenu=Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="View",menu=self.viewmenu)
        self.viewmenu.add_checkbutton(label="Show workpiece zero",\
                                      variable=self.CanvasContent.toggle_wp_zero,\
                                      command=self.CanvasContent.plot_wp_zero)
        self.viewmenu.add_checkbutton(label="Show all path directions",\
                                      variable=self.CanvasContent.toggle_start_stop,\
                                      command=self.CanvasContent.plot_cut_info)
        self.viewmenu.add_checkbutton(label="Show disabled shapes",\
                                      variable=self.CanvasContent.toggle_show_disabled,\
                                      command=self.CanvasContent.show_disabled)
            
        self.viewmenu.add_separator()
        self.viewmenu.add_command(label='Autoscale',command=self.Canvas.autoscale)

        self.viewmenu.add_separator()
        self.viewmenu.add_command(label='Delete Route',command=self.del_route_and_menuentry)         

        self.viewmenu.entryconfig(0,state=DISABLED)
        self.viewmenu.entryconfig(1,state=DISABLED)
        self.viewmenu.entryconfig(2,state=DISABLED)
        self.viewmenu.entryconfig(4,state=DISABLED)
        self.viewmenu.entryconfig(6,state=DISABLED)

        self.optionmenu=Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="Options",menu=self.optionmenu)
        self.optionmenu.add_command(label="Set tolerances", command=self.Get_Cont_Tol)
        self.optionmenu.add_separator()
        self.optionmenu.add_command(label="Scale contours", command=self.Get_Cont_Scale)
        self.optionmenu.add_command(label="Move workpiece zero", command=self.Move_WP_zero)
        self.optionmenu.entryconfig(2,state=DISABLED)
        self.optionmenu.entryconfig(3,state=DISABLED)
        
        
        self.helpmenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="Help", menu=self.helpmenu)
        self.helpmenu.add_command(label="About...", command=self.Show_About)

    def Get_Load_File(self):
        myFormats = [('AutoCAD / QCAD Drawing','*.dxf'),\
        ('All File','*.*') ]
        inidir=self.config.load_path
        filename = askopenfile(initialdir=inidir,\
                               filetypes=myFormats)
        if not filename:
            return
        else:
            self.load_filename=filename.name
            
        self.Load_File(self.load_filename)

    def Load_File(self,filename):
   
        self.textbox.text.delete(7.0,END)
        self.textbox.prt('\nLoading file: %s ' %filename)
        
        self.values=dxf_import.Load_DXF(filename,self.config,self.textbox)
        
        self.textbox.prt('\nLoaded layers: ' +str(len(self.values.layers)))
        self.textbox.prt('\nLoaded blocks: ' +str(len(self.values.blocks.Entities)))
        for i in range(len(self.values.blocks.Entities)):
            layers=self.values.blocks.Entities[i].get_used_layers()
            self.textbox.prt('\nBlock ' +str(i) +' includes '+str(len(self.values.blocks.Entities[i].geo))\
                             +' Geometries, reduced to ' +str(len(self.values.blocks.Entities[i].cont)) \
                             +' Contours, used layers: ' +str(layers))
        layers=self.values.entities.get_used_layers()
        insert_nr=self.values.entities.get_insert_nr()
        self.textbox.prt('\nLoaded ' +str(len(self.values.entities.geo))\
                             +' Entities geometries, reduced to ' +str(len(self.values.entities.cont))\
                             +' Contours, used layers: ' +str(layers)\
                             +' ,Number of inserts: ' +str(insert_nr))

        self.cont_scale=1.0
        
        self.cont_dx=0.0
        self.cont_dy=0.0

        self.viewmenu.entryconfig(0,state=NORMAL)
        self.viewmenu.entryconfig(1,state=NORMAL)
        self.viewmenu.entryconfig(2,state=NORMAL)
        self.viewmenu.entryconfig(4,state=NORMAL)

        self.exportmenu.entryconfig(0,state=NORMAL)

        self.optionmenu.entryconfig(2,state=NORMAL)
        self.optionmenu.entryconfig(3,state=NORMAL)        

        self.CanvasContent.makeplot(self.values)

        self.del_route_and_menuentry()
            
    def Get_Cont_Tol(self):

        title='Contour tolerances'
        label=(("Tolerance for common points [mm]:"),\
               ("Tolerance for curve fitting [mm]:"))
        value=(self.config.points_tolerance.get(),self.config.fitting_tolerance.get())
        dialog=Tkinter_Variable_Dialog(self.master,title,label,value)
        self.config.points_tolerance.set(dialog.result[0])
        self.config.fitting_tolerance.set(dialog.result[1])
        
        if self.load_filename==None:
            return
        self.Load_File(self.load_filename)
        self.textbox.prt(("\nSet new Contour tolerances (Pts: %0.3f, Fit: %0.3f) reloaded file"\
                              %(dialog.result[0],dialog.result[1])))
        
    def Get_Cont_Scale(self):
        old_scale=self.cont_scale
                
        value=askfloat('Scale Contours','Set the scale factor',\
                                initialvalue=self.cont_scale)
        if value==None:
            return
        
        self.cont_scale=value

        self.textbox.prt(("\nScaled Contours by factor %0.3f" %self.cont_scale))

        self.Canvas.scale_contours(self.cont_scale/old_scale)        
        
    def Move_WP_zero(self):
        old_dx=self.cont_dx
        old_dy=self.cont_dy

        title='Workpiece zero offset'
        label=(("Offset %s axis by mm:" %self.config.ax1_letter),\
               ("Offset %s axis by mm:" %self.config.ax2_letter))
        value=(self.cont_dx,self.cont_dy)
        dialog=Tkinter_Variable_Dialog(self.master,title,label,value)

        if dialog.result==False:
            return
        
        self.cont_dx=dialog.result[0]
        self.cont_dy=dialog.result[1]

        self.textbox.prt(("\nWorpiece zero offset: %s %0.2f; %s %0.2f" \
                              %(self.config.ax1_letter,self.cont_dx,
                                self.config.ax2_letter,self.cont_dy)))

        self.Canvas.move_wp_zero(self.cont_dx-old_dx,self.cont_dy-old_dy)

    def Get_Save_File(self):

        if self.load_filename==None:
            showwarning("Export G-Code", "Nothing to export!")
            return
        
        myFormats = [('G-Code for EMC2','*.ngc'),\
        ('All File','*.*') ]

        (beg, ende)=os.path.split(self.load_filename)
        (fileBaseName, fileExtension)=os.path.splitext(ende)

        inidir=self.config.save_path
        self.save_filename = asksaveasfilename(initialdir=inidir,\
                               initialfile=fileBaseName +'.ngc',filetypes=myFormats)

    def Write_GCode(self):
        
        tempfile_rw = self.config.tempfile_rw         
        editfile = self.config.editfilename
        
        delete_e = open(editfile, "w")
        delete_e.write("")
        delete_e.close()       
        
        outlog = open(editfile, "a")
        edit_readline = open(tempfile_rw, "r")
        for ew in edit_readline: 
            outlog.write(ew)
        outlog.write("M2")
        outlog.close()
        edit_readline.close() 
        
        readline = open(tempfile_rw, "r")    
        for w in readline: 
            print w       
        print'M2'
        readline.close()
                
        delete_t = open(tempfile_rw, "w")
        delete_t.write("")
        delete_t.close()
        
        self.ende()          
            
    def Add_to_File(self):

        self.opt_export_route()

        status=1

        config=self.config
        postpro=self.postpro

        postpro.write_gcode_be(self.ExportParas,self.load_filename)

        for nr in range(1,len(self.TSP.opt_route)):
            shape=self.shapes_to_write[self.TSP.opt_route[nr]]
            self.textbox.prt(("\nWriting Shape: %s" %shape),1)
                
            if not(shape.nr in self.CanvasContent.Disabled):
                stat =shape.Write_GCode(config,postpro)
                status=status*stat

        string=postpro.write_gcode_en(self.ExportParas)

        if status==1:
            self.textbox.prt(("\nSuccessfully generated G-Code"))
            self.master.update_idletasks()

        else:
            self.textbox.prt(("\nError during G-Code Generation"))
            self.master.update_idletasks()

################################################################################вывод программы
        save_file = self.config.tempfile_gcode
        f = open(save_file, "w")
        f.write(string)
        f.close()
        
        f = open(save_file, "r")  
        lines = f.readlines()
        f.close()
        ch = '' 
        ch1 = ''
        program = ''
        x_max, p, q, d, k, i, f, j, s, l, t = 0, 1, 15, 1.5, 0.3, 1, 433, 0, 0, 1, 0101
        Dtr, Lng, Prk = 0, 0, 0
        N_start_end = []
        Z_start = []
        for l in lines:
            if  re.search("[^\(\)\.\-\+NGZXRIK\d\s]",l.upper()):
                l=str(re.sub("^\s+|\n|\r|\s+$", '', l.upper(),re.I))
                ch1 +=l
                ch1 +='\n'
            elif  re.search("G\s*([0-3.]+)", l.upper() ,re.I):
                if not  re.search("[^\(\)\.\-\+NGZXRIK\d\s]",l.upper()):
                    l=re.sub("^\s+|\n|\r|\s+$", '', l.upper(),re.I)
                    ch +='('
                    ch +=l
                    ch +=')'
                    ch +='\n'
                    p1 = N_start_end.append(int(re.search("N\s*([-0-9.]+)",l.upper(), re.I).group(1)))
                    z_st = Z_start.append(float(re.search("Z\s*([-0-9.]+)",l.upper(), re.I).group(1)))
                    x_max_sr = float(re.search("X\s*([-0-9.]+)",l.upper(), re.I).group(1))
                    if x_max_sr > x_max:
                        x_max = x_max_sr + 5
                    z_max = float(re.search("Z\s*([-0-9.]+)",l.upper(), re.I).group(1))
                        
        p = N_start_end[0]
        q = N_start_end[-1]
        z0 = Z_start[0]
        d = float(self.ExportParas.d_D.get())
        k = float(self.ExportParas.d_K.get())
        i = float(self.ExportParas.d_I.get())
        f = float(self.ExportParas.d_F.get())
        s = float(self.ExportParas.d_S.get())
        l = float(self.ExportParas.d_L.get())
        t = str(self.ExportParas.d_T.get())
        rb = self.ExportParas.g71_72.get()

        Dtr = float(self.ExportParas.D_out.get())
        Lng = float(self.ExportParas.Lg.get())
        Prk = float(self.ExportParas.D_in.get())
        checkbutton = self.ExportParas.only.get()
        show_blank = self.ExportParas.show_blank.get()
        code = 'G71.2'
        start_point = str('G1 X%s  Z%s \n' % (x_max, z0))
        if rb :
            code = 'G72.2'
            start_point = str('G1 X%s  Z%s \n' % (x_max, z_max))
        if checkbutton :
            j = 1           
        program += ch1
        blank = str('(AXIS,blank,%s,%s,%s)\n' % (Dtr, Lng, Prk))
        if show_blank :
            program += blank
        program += start_point
        stt = str('%s P%s Q%s  D%s K%s I%s F%s J%s S%s L%s \n' % (code,p,q,d,k,i,f,j,s,l,))
        program += stt
        program += ch
               

        
        tempfile_rw = self.config.tempfile_rw
        rw = open(tempfile_rw, "a")
        rw.write(program)
        rw.close()
                    

    def opt_export_route(self):
        
        iter =min(self.config.max_iterations,len(self.CanvasContent.Shapes)*20)
        
        self.shapes_to_write=[]
        shapes_st_en_points=[]
        
        for shape_nr in range(len(self.CanvasContent.Shapes)):
            shape=self.CanvasContent.Shapes[shape_nr]
            if not(shape.nr in self.CanvasContent.Disabled):
                self.shapes_to_write.append(shape)
                shapes_st_en_points.append(shape.get_st_en_points())
                

        x_st=self.config.axis1_st_en.get()
        y_st=self.config.axis2_st_en.get()
        start=PointClass(x=x_st,y=y_st)
        ende=PointClass(x=x_st,y=y_st)
        shapes_st_en_points.append([start,ende])

        self.textbox.prt(("\nTSP Starting"),1)
                
        self.TSP=tsp.TSPoptimize(shapes_st_en_points,self.textbox,self.master,self.config)
        self.textbox.prt(("\nTSP start values initialised"),1)

        for it_nr in range(iter):
            if (it_nr%10)==0:
                self.textbox.prt(("\nTSP Iteration nr: %i" %it_nr),1)
                for hdl in self.CanvasContent.path_hdls:
                    self.Canvas.canvas.delete(hdl)
                self.CanvasContent.path_hdls=[]
                self.CanvasContent.plot_opt_route(shapes_st_en_points,self.TSP.opt_route)
                self.master.update_idletasks()
                
            self.TSP.calc_next_iteration()
            
        self.textbox.prt(("\nTSP done with result:"),1)
        self.textbox.prt(("\n%s" %self.TSP),1)

        self.viewmenu.entryconfig(6,state=NORMAL)        

    def del_route_and_menuentry(self):
        try:
            self.viewmenu.entryconfig(6,state=DISABLED)
            self.CanvasContent.delete_opt_path()
        except:
            pass
        
    def Show_About(self):
        Show_About_Info(self.master)
  
    def ende(self):
        self.master.destroy()
        self.master.quit()

class TextboxClass:
    def __init__(self,frame=None,master=None,DEBUG=0):
            
        self.DEBUG=DEBUG
        self.master=master
        self.text = Text(frame,height=7)
        
        self.textscr = Scrollbar(frame)
        self.text.grid(row=0,column=0,pady=4,sticky=E+W)
        self.textscr.grid(row=0,column=1,pady=4,sticky=N+S)
        frame.columnconfigure(0,weight=1)
        frame.columnconfigure(1,weight=0)

        
        self.text.bind("<Button-3>", self.text_contextmenu)

        self.textscr.config(command=self.text.yview)
        self.text.config(yscrollcommand=self.textscr.set)
        self.prt('Program started\nVersion V0.1LatheG71\n')

    def set_debuglevel(self,DEBUG=0):
        self.DEBUG=DEBUG
        if DEBUG:
            self.text.config(height=15)

    def prt(self,txt='',DEBUGLEVEL=0):

        if self.DEBUG>=DEBUGLEVEL:
            self.text.insert(END,txt)
            self.text.yview(END)
            self.master.update_idletasks()
            

    def text_contextmenu(self,event):

        popup = Menu(self.text,tearoff=0)        
        popup.add_command(label='Delete text entries',command=self.text_delete_entries)
        popup.post(event.x_root, event.y_root)
        
    def text_delete_entries(self):
        self.text.delete(7.0,END)
        self.text.yview(END)           

class ExportParasClass:
    def __init__(self,master=None,config=None,postpro=None):
        self.master=master
  
        self.nb = NotebookClass(self.master,width=280)

        self.nb_f1 = Frame(self.nb())
        self.nb_f2 = Frame(self.nb())
        self.nb_f3 = Frame(self.nb())
        
        self.nb.add_screen(self.nb_f1, "Parameter")
        self.nb.add_screen(self.nb_f2, "Gcode    ")
        self.nb.add_screen(self.nb_f3, "Img      ")
        
        self.nb_f1.columnconfigure(0,weight=1)
        self.nb_f2.columnconfigure(0,weight=1)        
        self.nb_f3.columnconfigure(0,weight=1) 
    
        self.erstelle_eingabefelder(config)
        self.erstelle_textfelder(config )

        self.gcode_be.insert(END,postpro.gcode_be)
        self.gcode_en.insert(END,postpro.gcode_en)

        self.ccc = CanvasContentClass(self,Canvas,config)# ????????????????????????????????????????????????
        

        


        
    def erstelle_eingabefelder(self,config):
       
        f1=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f1.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        f2=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f2.grid(row=1,column=0,padx=2,pady=2,sticky=N+W+E)
        f3=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f3.grid(row=2,column=0,padx=2,pady=2,sticky=N+W+E)
        f4=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f4.grid(row=3,column=0,padx=2,pady=2,sticky=N+W+E)
            
        f1.columnconfigure(0,weight=1)
        f2.columnconfigure(0,weight=1)
        f3.columnconfigure(0,weight=1) 
        f4.columnconfigure(0,weight=1)         
#########################################################################################параметры в окне              
        Label(f1, text="Depth of cut   [D]")\
                .grid(row=0,column=0,sticky=N+W,padx=4)
        self.d_D = Entry(f1,width=7,textvariable=config.depth_D)
        self.d_D.grid(row=0,column=1,sticky=N+E)
             
        Label(f1, text="Finishing(depth)      [K]")\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        self.d_K = Entry(f1,width=7,textvariable=config.finishing_depth)
        self.d_K.grid(row=1,column=1,sticky=N+E)        

        Label(f1, text=("Quantity      [I]" ))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        self.d_I = Entry(f1,width=7,textvariable=config.quantity_I)
        self.d_I.grid(row=2,column=1,sticky=N+E)
        

        Label(f2, text=("Feedrate   [F]"))\
                .grid(row=0,column=0,sticky=N+W,padx=4)
        self.d_F = Entry(f2,width=7,textvariable=config.feedrate_F)
        self.d_F.grid(row=0,column=1,sticky=N+E)

        Label(f2, text=("Ending Block  [Q]"))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        self.d_Q = Entry(f2,width=7,textvariable=config.ending_block_Q)
        self.d_Q.grid(row=1,column=1,sticky=N+E)

        Label(f2, text=("Start_Z  [Z0]"))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        self.d_Z0 = Entry(f2,width=7,textvariable=config.start_Z0)
        self.d_Z0.grid(row=2,column=1,sticky=N+E)
        
        Label(f2, text=("reserve  [S]" ))\
                .grid(row=3,column=0,sticky=N+W,padx=4)
        self.d_S = Entry(f2,width=7,textvariable=config.reserve_S)
        self.d_S.grid(row=3,column=1,sticky=N+E)

        Label(f2, text=("Tool  [T]" ))\
                .grid(row=4,column=0,sticky=N+W,padx=4)
        self.d_T = Entry(f2,width=7,textvariable=config.tool_T)
        self.d_T.grid(row=4,column=1,sticky=N+E)


        Label(f2, text=("reserve  [L]" ))\
                .grid(row=5,column=0,sticky=N+W,padx=4)
        self.d_L = Entry(f2,width=7,textvariable=config.reserve_L)  
        self.d_L.grid(row=5,column=1,sticky=N+E)

                               
        self.g71_72=IntVar()
        self.g71_72.set(0)
        self.only=IntVar()
        self.show_blank=IntVar()
        self.show_blank.set(1)
        
        Label(f3, text=("G71" ))\
        .grid(row=3,column=0,sticky=N+W,padx=4)
        self.rad0 = Radiobutton(f3,text="G71",variable=self.g71_72,value=0 ,command=lambda: self.change_img71())
        self.rad0.grid(row=3,column=1,sticky=N+E)
        
        Label(f3, text=("G72" ))\
        .grid(row=4,column=0,sticky=N+W,padx=4)        
        self.rad1 = Radiobutton(f3,text="G72",variable=self.g71_72,value=1,command=lambda: self.change_img72())
        self.rad1.grid(row=4,column=1,sticky=N+E)
        
        Label(f3, text=("Only finishing [J]" ))\
        .grid(row=5,column=0,sticky=N+W,padx=4)        
        self.rad2 = Checkbutton(f3,text="",variable=self.only,onvalue=1,offvalue=0)
        self.rad2.grid(row=5,column=1,sticky=N+E)
        
        
        Label(f4, text="Diameter blank outside")\
        .grid(row=0,column=0,sticky=N+W,padx=4)
        self.D_out = Entry(f4,width=7,textvariable=config.b_D_out)
        self.D_out.grid(row=0,column=1,sticky=N+E)
             
        Label(f4, text="Lenght blank")\
        .grid(row=1,column=0,sticky=N+W,padx=4)
        self.Lg = Entry(f4,width=7,textvariable=config.b_L)
        self.Lg.grid(row=1,column=1,sticky=N+E)        

        Label(f4, text=("Blank diam. inside" ))\
        .grid(row=2,column=0,sticky=N+W,padx=4)
        self.D_in = Entry(f4,width=7,textvariable=config.b_D_in)
        self.D_in.grid(row=2,column=1,sticky=N+E)
        
        Label(f4, text=("Show blank" ))\
        .grid(row=3,column=0,sticky=N+W,padx=4)        
        self.rad3 = Checkbutton(f4,text="",variable=self.show_blank,onvalue=1,offvalue=0)
        self.rad3.grid(row=3,column=1,sticky=N+E)
        
    def revers_contour(self):
        aa=self.ccc.switch_shape_dir()# ????????????????????????????????????????????????
 
    def change_img71( self): #при выборе 71-72 меняем картинки
        self.textbox.prt('\ncheckbutton is OK!!')
        self.im = PhotoImage(file='/home/nkp/dxf/G71.gif') 
        f33=Frame(self.nb_f3,relief = FLAT,bd = 1)
        f33.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        f33.columnconfigure(0,weight=1) 

        self.gif = Label(f33 , image=self.im)
        self.gif.grid(row=0,column=0,columnspan=2,sticky=N+W,padx=2)


        f33.columnconfigure(0,weight=1)
        f33.rowconfigure(1,weight=0)
        f33.rowconfigure(3,weight=0)
        
    def change_img72( self):
        self.im = PhotoImage(file='/home/nkp/dxf/G72.gif') 
        f33=Frame(self.nb_f3,relief = FLAT,bd = 1)
        f33.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        f33.columnconfigure(0,weight=1) 

        self.gif = Label(f33 , image=self.im)
        self.gif.grid(row=0,column=0,columnspan=2,sticky=N+W,padx=2)


        f33.columnconfigure(0,weight=1)
        f33.rowconfigure(1,weight=0)
        f33.rowconfigure(3,weight=0) 
        
    def erstelle_textfelder(self,config):
        f22=Frame(self.nb_f2,relief = FLAT,bd = 1)
        f22.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        f22.columnconfigure(0,weight=1)        

        Label(f22 , text="G-Code at the begin of file")\
                .grid(row=0,column=0,columnspan=2,sticky=N+W,padx=2)
        self.gcode_be = Text(f22,width=10,height=8)
        self.gcode_be_sc = Scrollbar(f22)
        self.gcode_be.grid(row=1,column=0,pady=2,sticky=E+W)
        self.gcode_be_sc.grid(row=1,column=1,padx=2,pady=2,sticky=N+S)
        self.gcode_be_sc.config(command=self.gcode_be.yview)
        self.gcode_be.config(yscrollcommand=self.gcode_be_sc.set)

        Label(f22, text="G-Code at the end of file")\
                .grid(row=2,column=0,columnspan=2,sticky=N+W,padx=2)
        self.gcode_en = Text(f22,width=10,height=5)
        self.gcode_en_sc = Scrollbar(f22)
        self.gcode_en.grid(row=3,column=0,pady=2,sticky=E+W)
        self.gcode_en_sc.grid(row=3,column=1,padx=2,pady=2,sticky=N+S)
        self.gcode_en_sc.config(command=self.gcode_en.yview)
        self.gcode_en.config(yscrollcommand=self.gcode_en_sc.set)

        f22.columnconfigure(0,weight=1)
        f22.rowconfigure(1,weight=0)
        f22.rowconfigure(3,weight=0)
# вкладка Img
 
        f33=Frame(self.nb_f3,relief = FLAT,bd = 1)
        f33.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        f33.columnconfigure(0,weight=1)
        self.im = PhotoImage(file='/home/nkp/dxf/G71.gif')  
        self.gif = Label(f33 , image=self.im)
        self.gif.grid(row=0,column=0,columnspan=2,sticky=N+W,padx=2)


        f33.columnconfigure(0,weight=1)
        f33.rowconfigure(1,weight=0)
        f33.rowconfigure(3,weight=0)
      

 
class CanvasClass:
    def __init__(self, master = None,text=None):
        
        self.master=master
        self.Content=[]

        self.lastevent=[]
        self.sel_rect_hdl=[]
        self.dir_var = IntVar()
        self.dx=0.0
        self.dy=0.0
        self.scale=1.0


        self.label=Label(self.master, text="Curser Coordinates: X=0.0, Y=0.0, Scale: 1.00",bg="white",anchor="w")
        self.label.grid(row=1,column=0,sticky=E+W)
        
        self.var = IntVar()
        self.cbutt = Checkbutton(self.master,text="Revers",variable=self.var,command=lambda: self.Content.switch_shape_dir)
        self.cbutt.grid(row=2,column=1,sticky=E+W)
        
        self.canvas=Canvas(self.master,width=650,height=500, bg = "white")
        self.canvas.grid(row=0,column=0,sticky=N+E+S+W)
        self.master.columnconfigure(0,weight=1)
        self.master.rowconfigure(0,weight=1)
        for i in range(25):
            self.canvas.create_oval(5+(4*i),5+(3*i),(5*i)+60,(i)+60, fill='gray70')

        self.canvas.bind("<Motion>", self.moving)

        self.canvas.bind("<Button-1>", self.select_cont)
        
        self.canvas.bind("<Shift-Button-1>", self.multiselect_cont)
        self.canvas.bind("<B1-Motion>", self.select_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.select_release)

        self.canvas.bind("<Button-3>", self.make_contextmenu)

        self.canvas.bind("<Control-Button-1>", self.mouse_move)
        self.canvas.bind("<Control-B1-Motion>", self.mouse_move_motion)
        self.canvas.bind("<Control-ButtonRelease-1>", self.mouse_move_release)
        self.canvas.bind("<Control-Button-3>", self.mouse_zoom)
        self.canvas.bind("<Control-B3-Motion>", self.mouse_zoom_motion)
        self.canvas.bind("<Control-ButtonRelease-3>", self.mouse_zoom_release) 
          
    def revers_contour(self,event):
        a=self.Content.select_cont


    def moving(self,event):
        x=self.dx+(event.x/self.scale)
        y=self.dy+(self.canvas.winfo_height()-event.y)/self.scale

        if self.scale<1:
            self.label['text']=("Curser Coordinates: X= %5.0f Y= %5.0f , Scale: %5.3f" \
                                %(x,y,self.scale))
            
        elif (self.scale>=1)and(self.scale<10):      
            self.label['text']=("Curser Coordinates: X= %5.1f Y= %5.1f , Scale: %5.2f" \
                                %(x,y,self.scale))
        elif self.scale>=10:      
            self.label['text']=("Curser Coordinates: X= %5.2f Y= %5.2f , Scale: %5.1f" \
                                %(x,y,self.scale))
        
    def select_cont(self,event):
        self.schliesse_contextmenu()
        
        self.moving(event)
        self.Content.deselect()
        self.sel_rect_hdl=Rectangle(self.canvas,event.x,event.y,event.x,event.y,outline="grey") 
        self.lastevent=event

    def multiselect_cont(self,event):
        self.schliesse_contextmenu()
        
        self.sel_rect_hdl=Rectangle(self.canvas,event.x,event.y,event.x,event.y,outline="grey") 
        self.lastevent=event

    def select_rectangle(self,event):
        self.moving(event)
        self.canvas.coords(self.sel_rect_hdl,self.lastevent.x,self.lastevent.y,\
                           event.x,event.y)

    def select_release(self,event):
 
        dx=self.lastevent.x-event.x
        dy=self.lastevent.y-event.y
        self.canvas.delete(self.sel_rect_hdl)
        
        
        if (abs(dx)+abs(dy))>6:
            items=self.canvas.find_overlapping(event.x,event.y,event.x+dx,event.y+dy)
            mode='multi'
        else:
            items=self.canvas.find_overlapping(event.x-3,event.y-3,event.x+3,event.y+3)
            mode='single'
            
        self.Content.addselection(items,mode)

    def mouse_move(self,event):
        self.master.config(cursor="fleur")
        self.lastevent=event

    def mouse_move_motion(self,event):
        self.moving(event)
        dx=event.x-self.lastevent.x
        dy=event.y-self.lastevent.y
        self.dx=self.dx-dx/self.scale
        self.dy=self.dy+dy/self.scale
        self.canvas.move(ALL,dx,dy)
        self.lastevent=event

    def mouse_move_release(self,event):
        self.master.config(cursor="")      

    def mouse_zoom(self,event):
        self.canvas.focus_set()
        self.master.config(cursor="sizing")
        self.firstevent=event
        self.lastevent=event

    def mouse_zoom_motion(self,event):
        self.moving(event)
        dy=self.lastevent.y-event.y
        sca=(1+(dy*3)/float(self.canvas.winfo_height()))
       
        self.dx=(self.firstevent.x+((-self.dx*self.scale)-self.firstevent.x)*sca)/sca/-self.scale
        eventy=self.canvas.winfo_height()-self.firstevent.y
        self.dy=(eventy+((-self.dy*self.scale)-eventy)*sca)/sca/-self.scale
        
        self.scale=self.scale*sca
        self.canvas.scale( ALL, self.firstevent.x,self.firstevent.y,sca,sca)
        self.lastevent=event

        self.Content.plot_cut_info() 
        self.Content.plot_wp_zero()

    def mouse_zoom_release(self,event):
        self.master.config(cursor="")
                
    def make_contextmenu(self,event):
        self.lastevent=event

        self.schliesse_contextmenu()
            
        popup = Menu(self.canvas,tearoff=0)
        self.popup=popup
        popup.add_command(label='Invert Selection',command=self.Content.invert_selection)
        popup.add_command(label='Disable Selection',command=self.Content.disable_selection)
        popup.add_command(label='Enable Selection',command=self.Content.enable_selection)

        popup.add_separator()
        popup.add_command(label='Switch Direction',command=self.Content.switch_shape_dir)
        
        self.dir_var.set(self.Content.calc_dir_var())
        cut_cor_menu = Menu(popup,tearoff=0)
        cut_cor_menu.add_checkbutton(label="G40 No correction",\
                                     variable=self.dir_var,onvalue=0,\
                                     command=lambda:self.Content.set_cut_cor(40))
        cut_cor_menu.add_checkbutton(label="G41 Cutting left",\
                                     variable=self.dir_var,onvalue=1,\
                                     command=lambda:self.Content.set_cut_cor(41))
        cut_cor_menu.add_checkbutton(label="G42 Cutting right",\
                                     variable=self.dir_var,onvalue=2,\
                                     command=lambda:self.Content.set_cut_cor(42))
        popup.add_cascade(label='Set Cutter Correction',menu=cut_cor_menu)

        if len(self.Content.Selected)==0:
            popup.entryconfig(0,state=DISABLED)
            popup.entryconfig(1,state=DISABLED)
            popup.entryconfig(2,state=DISABLED)
            popup.entryconfig(4,state=DISABLED)
            popup.entryconfig(5,state=DISABLED)

        popup.post(event.x_root, event.y_root)
        
    def schliesse_contextmenu(self):
        try:
            self.popup.destroy()
            del(self.popup)
        except:
            pass

    def autoscale(self):

        rand=20

        self.canvas.move(ALL,self.dx*self.scale,-self.canvas.winfo_height()-self.dy*self.scale)
        self.dx=0;
        self.dy=-self.canvas.winfo_height()/self.scale

        d=self.canvas.bbox(ALL)
        cx=(d[0]+d[2])/2
        cy=(d[1]+d[3])/2
        dx=d[2]-d[0]
        dy=d[3]-d[1]

        xs=float(dx)/(self.canvas.winfo_width()-rand)
        ys=float(dy)/(self.canvas.winfo_height()-rand)
        scale=1/max(xs,ys)
        
        self.canvas.scale( ALL,0,0,scale,scale)
        self.scale=self.scale*scale

        dx=self.canvas.winfo_width()/2-cx*scale
        dy=self.canvas.winfo_height()/2-cy*scale
        self.dy=self.dy/scale
        self.dx=self.dx/scale
        self.canvas.move(ALL,dx,dy)
        
        self.dx=self.dx-dx/self.scale
        self.dy=self.dy+dy/self.scale

        self.Content.plot_cut_info()
        self.Content.plot_wp_zero()
        
    def get_can_coordinates(self,x_st,y_st):
        x_ca=(x_st-self.dx)*self.scale
        y_ca=(y_st-self.dy)*self.scale-self.canvas.winfo_height()
        return x_ca, y_ca

    def scale_contours(self,delta_scale):     
        self.scale=self.scale/delta_scale
        self.dx=self.dx*delta_scale
        self.dy=self.dy*delta_scale

        event=PointClass(x=0,y=0)
        self.moving(event)

        for shape in self.Content.Shapes:
            shape.sca[0]=shape.sca[0]*delta_scale
            shape.sca[1]=shape.sca[1]*delta_scale
            shape.sca[2]=shape.sca[2]*delta_scale
            
            shape.p0=shape.p0*[delta_scale,delta_scale]

    def move_wp_zero(self,delta_dx,delta_dy):
        self.dx=self.dx-delta_dx
        self.dy=self.dy-delta_dy

        for shape in self.Content.Shapes:
            shape.p0-=PointClass(x=delta_dx,y=delta_dy)

        self.Content.plot_wp_zero()
        
class CanvasContentClass:
    def __init__(self,Canvas,textbox,config):
        self.Canvas=Canvas
        self.textbox=textbox
        self.config=config
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitieContents=[]
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]
        

        self.toggle_wp_zero=IntVar()
        self.toggle_wp_zero.set(1)

        self.toggle_start_stop=IntVar()
        self.toggle_start_stop.set(1) #показывать стрелки направления контура при старте

        self.toggle_show_disabled=IntVar()
        self.toggle_show_disabled.set(0)  
        
    def __str__(self):
        s='\nNr. of Shapes ->'+str(len(self.Shapes))
        for lay in self.LayerContents:
            s=s+'\n'+str(lay)
        for ent in self.EntitieContents:
            s=s+'\n'+str(ent)
        s=s+'\nSelected ->'+str(self.Selected)\
           +'\nDisabled ->'+str(self.Disabled)
        return s

    def calc_dir_var(self):
        if len(self.Selected)==0:
            return -1
        dir=self.Shapes[self.Selected[0]].cut_cor
        for shape_nr in self.Selected[1:len(self.Selected)]: 
            if not(dir==self.Shapes[shape_nr].cut_cor):
                return -1   
        return dir-40
                
    def makeplot(self,values):
        self.values=values

        self.Canvas.canvas.delete(ALL)
        
        self.Canvas.scale=1
        self.Canvas.dx=0
        self.Canvas.dy=-self.Canvas.canvas.winfo_height()

        self.Shapes=[]
        self.LayerContents=[]
        self.EntitieContents=[]
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]

        self.make_shapes(p0=PointClass(x=0,y=0),sca=[1,1,1])
        self.plot_shapes()
        self.LayerContents.sort()
        self.EntitieContents.sort()

        self.Canvas.autoscale()

    def make_shapes(self,ent_nr=-1,p0=PointClass(x=0,y=0),sca=[1,1,1]):
        if ent_nr==-1:
            entities=self.values.entities
        else:
            entities=self.values.blocks.Entities[ent_nr]
        ent_geos=entities.geo
        cont=entities.cont
        for c_nr in range(len(cont)):
            if ent_geos[cont[c_nr].order[0][0]].Typ=="Insert":
                ent_geo=ent_geos[cont[c_nr].order[0][0]]
                self.make_shapes(ent_geo.Block,ent_geo.Point,ent_geo.Scale)
            else:
                self.Shapes.append(ShapeClass(len(self.Shapes),ent_nr,c_nr,cont[c_nr].closed,p0,sca[:],40,cont[c_nr].length*sca[0],[],[]))
                for ent_geo_nr in range(len(cont[c_nr].order)):
                    ent_geo=ent_geos[cont[c_nr].order[ent_geo_nr][0]]
                    if cont[c_nr].order[ent_geo_nr][1]:
                        ent_geo.geo.reverse()
                        for geo in ent_geo.geo:
                            geo=copy(geo)
                            geo.reverse()
                            self.Shapes[-1].geos.append(geo)

                        ent_geo.geo.reverse()
                    else:
                        for geo in ent_geo.geo:
                            self.Shapes[-1].geos.append(copy(geo))
                        
                self.addtoLayerContents(self.Shapes[-1].nr,ent_geo.Layer_Nr)
                self.addtoEntitieContents(self.Shapes[-1].nr,ent_nr,c_nr)
                
                lns=len(self.Shapes[-1].geos) - 1
                bx=self.Shapes[-1].geos[0].Pa.x
                ex=self.Shapes[-1].geos[lns].Pe.x

                if bx < ex:
                    self.switch_shape_dir()#XXX
                bx=self.Shapes[-1].geos[0].Pa.x
                ex=self.Shapes[-1].geos[0].Pe.x
                    
    def plot_shapes(self):
        for shape in self.Shapes:
            shape.plot2can(self.Canvas.canvas)
            
    def plot_wp_zero(self):
        for hdl in self.wp_zero_hdls:
            self.Canvas.canvas.delete(hdl) 
        self.wp_zero_hdls=[]
        if self.toggle_wp_zero.get(): 
            x_zero,y_zero=self.Canvas.get_can_coordinates(0,0)
            xy=x_zero-8,-y_zero-8,x_zero+8,-y_zero+8
            hdl=Oval(self.Canvas.canvas,xy,outline="gray")
            self.wp_zero_hdls.append(hdl)

            xy=x_zero-6,-y_zero-6,x_zero+6,-y_zero+6
            hdl=Arc(self.Canvas.canvas,xy,start=0,extent=180,style="pieslice",outline="gray")
            self.wp_zero_hdls.append(hdl)
            hdl=Arc(self.Canvas.canvas,xy,start=90,extent=180,style="pieslice",outline="gray")
            self.wp_zero_hdls.append(hdl)
            hdl=Arc(self.Canvas.canvas,xy,start=270,extent=90,style="pieslice",outline="gray",fill="gray")
            self.wp_zero_hdls.append(hdl)
    def plot_cut_info(self):
        for hdl in self.dir_hdls:
            self.Canvas.canvas.delete(hdl) 
        self.dir_hdls=[]
       
        if not(self.toggle_start_stop.get()):
            draw_list=self.Selected[:]
        else:
            draw_list=range(len(self.Shapes))    
        for shape_nr in draw_list:
            if not(shape_nr in self.Disabled):
                self.dir_hdls+=self.Shapes[shape_nr].plot_cut_info(self.Canvas,self.config)


    def plot_opt_route(self,shapes_st_en_points,route):
        for en_nr in range(len(route)):
            if en_nr==0:
                st_nr=-1
                col='gray'
            elif en_nr==1:
                st_nr=en_nr-1
                col='gray'
            else:
                st_nr=en_nr-1
                col='peru'
                
            st=shapes_st_en_points[route[st_nr]][1]
            en=shapes_st_en_points[route[en_nr]][0]

            x_ca_s,y_ca_s=self.Canvas.get_can_coordinates(st.x,st.y)
            x_ca_e,y_ca_e=self.Canvas.get_can_coordinates(en.x,en.y)

            self.path_hdls.append(Line(self.Canvas.canvas,x_ca_s,-y_ca_s,x_ca_e,-y_ca_e,fill=col,arrow='last'))
        self.Canvas.canvas.update()


    def addtoLayerContents(self,shape_nr,lay_nr):
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.Shapes.append(shape_nr)
                return

        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr,LayerName,[shape_nr]))
        
    def addtoEntitieContents(self,shape_nr,ent_nr,c_nr):
        
        for EntCon in self.EntitieContents:
            if EntCon.EntNr==ent_nr:
                if c_nr==0:
                    EntCon.Shapes.append([])
                
                EntCon.Shapes[-1].append(shape_nr)
                return

        if ent_nr==-1:
            EntName='Entities'
        else:
            EntName=self.values.blocks.Entities[ent_nr].Name
            
        self.EntitieContents.append(EntitieContentClass(ent_nr,EntName,[[shape_nr]]))

    def delete_opt_path(self):
        for hdl in self.path_hdls:
            self.Canvas.canvas.delete(hdl)
            
        self.path_hdls=[]
        
    def deselect(self): 
        self.set_shapes_color(self.Selected,'deselected')
        
        if not(self.toggle_start_stop.get()):
            for hdl in self.dir_hdls:
                self.Canvas.canvas.delete(hdl) 
            self.dir_hdls=[]
        
    def addselection(self,items,mode):
        for item in items:
            try:
                tag=int(self.Canvas.canvas.gettags(item)[-1])
                if not(tag in self.Selected):
                    self.Selected.append(tag)

                    self.textbox.prt('\n\nAdded shape to selection:'\
                                     +str(self.Shapes[tag]),3)
                    
                    if mode=='single':
                        break
            except:
                pass
 
        self.plot_cut_info()
        self.set_shapes_color(self.Selected,'selected')
 
    def invert_selection(self):
        new_sel=[]
        for shape_nr in range(len(self.Shapes)):
            if (not(shape_nr in self.Disabled)) & (not(shape_nr in self.Selected)):
                new_sel.append(shape_nr)

        self.deselect()
        self.Selected=new_sel
        self.set_shapes_color(self.Selected,'selected')
        self.plot_cut_info()

        self.textbox.prt('\nInverting Selection',3)
        

    def disable_selection(self):
        for shape_nr in self.Selected:
            if not(shape_nr in self.Disabled):
                self.Disabled.append(shape_nr)
        self.set_shapes_color(self.Selected,'disabled')
        self.Selected=[]
        self.plot_cut_info()

    def enable_selection(self):
        for shape_nr in self.Selected:
            if shape_nr in self.Disabled:
                nr=self.Disabled.index(shape_nr)
                del(self.Disabled[nr])
        self.set_shapes_color(self.Selected,'deselected')
        self.Selected=[]
        self.plot_cut_info()

    def show_disabled(self):
        if (self.toggle_show_disabled.get()==1):
            self.set_hdls_normal(self.Disabled)
            self.show_dis=1
        else:
            self.set_hdls_hidden(self.Disabled)
            self.show_dis=0
            
    def switch_shape_dir(self):
        #print "***************************"
        for shape_nr in range(len(self.Shapes)):
            self.Shapes[shape_nr].reverse()
            self.textbox.prt('\n\nSwitched Direction at Shape:'\
                             +str(self.Shapes[shape_nr]))
        self.plot_cut_info()

                
    def set_cut_cor(self,correction):
        for shape_nr in self.Selected: 
            self.Shapes[shape_nr].cut_cor=correction
            
            self.textbox.prt('\n\nChanged Cutter Correction at Shape:'\
                             +str(self.Shapes[shape_nr]),3)
        self.plot_cut_info() 
        
    def set_shapes_color(self,shape_nrs,state):
        s_shape_nrs=[]
        d_shape_nrs=[]
        for shape in shape_nrs:
            if not(shape in self.Disabled):
                s_shape_nrs.append(shape)
            else:
                d_shape_nrs.append(shape)
        
        s_hdls=self.get_shape_hdls(s_shape_nrs)
        d_hdls=self.get_shape_hdls(d_shape_nrs)
    
        if state=='deselected':
            s_color='black'
            d_color='gray'
            self.Selected=[]
        elif state=='selected':
            s_color='red'
            d_color='blue'
        elif state=='disabled':
            s_color='gray'
            d_color='gray'
            
        self.set_color(s_hdls,s_color)
        self.set_color(d_hdls,d_color)

        if (self.toggle_show_disabled.get()==0):
            self.set_hdls_hidden(d_shape_nrs)
        
    def set_color(self,hdls,color):
        for hdl in hdls:
            if (self.Canvas.canvas.type(hdl)=="oval") :
                self.Canvas.canvas.itemconfig(hdl, outline=color)
            else:
                self.Canvas.canvas.itemconfig(hdl, fill=color)

    def set_hdls_hidden(self,shape_nrs):
        hdls=self.get_shape_hdls(shape_nrs)
        for hdl in hdls:
            self.Canvas.canvas.itemconfig(hdl,state='hidden')

    def set_hdls_normal(self,shape_nrs):
        hdls=self.get_shape_hdls(shape_nrs)
        for hdl in hdls:
            self.Canvas.canvas.itemconfig(hdl,state='normal')            
        
    def get_shape_hdls(self,shape_nrs):        
        hdls=[]
        for s_nr in shape_nrs:
            if type(self.Shapes[s_nr].geos_hdls[0]) is list:
                for subcont in self.Shapes[s_nr].geos_hdls:
                    hdls=hdls+subcont
            else:
                hdls=hdls+self.Shapes[s_nr].geos_hdls
        return hdls      
                                       
       
class LayerContentClass:
    def __init__(self,LayerNr=None,LayerName='',Shapes=[]):
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.Shapes=Shapes
        
    def __cmp__(self, other):
         return cmp(self.LayerNr, other.LayerNr)

    def __str__(self):
        return '\nLayerNr ->'+str(self.LayerNr)+'\nLayerName ->'+str(self.LayerName)\
               +'\nShapes ->'+str(self.Shapes)
    
class EntitieContentClass:
    def __init__(self,EntNr=None,EntName='',Shapes=[]):
        self.EntNr=EntNr
        self.EntName=EntName
        self.Shapes=Shapes

    def __cmp__(self, other):
         return cmp(self.EntNr, other.EntNr)        
        
    def __str__(self):
        return '\nEntNr ->'+str(self.EntNr)+'\nEntName ->'+str(self.EntName)\
               +'\nShapes ->'+str(self.Shapes)

class ConfigClass:
    def __init__(self,textbox):
        self.folder=self.get_settings_folder(str(APPNAME))

        self.parser = ConfigParser.ConfigParser()
        self.cfg_file_name=APPNAME+'_config.cfg'
        self.parser.read(os.path.join(self.folder,self.cfg_file_name))

        if len(self.parser.sections())==0:
            self.make_new_Config_file()
            self.parser.read(os.path.join(self.folder,self.cfg_file_name))
            textbox.prt(('\nNo config file found generated new on at: %s' \
                             %os.path.join(self.folder,self.cfg_file_name)))
        else:
            textbox.prt(('\nLoading config file:%s' \
                             %os.path.join(self.folder,self.cfg_file_name)))

        self.get_all_vars()

        textbox.set_debuglevel(DEBUG=self.debug)
        textbox.prt('\nDebug Level: ' +str(self.debug),1)
        textbox.prt(str(self),1)

    def get_settings_folder(self,appname): 
 
        folder = os.path.join(os.getcwd(), appname) 

        try: 
            os.mkdir(folder) 
        except OSError: 
            pass 

        return folder 

    def make_new_Config_file(self):
        pass
            
    def get_all_vars(self):
        try:               
            self.tool_dia=DoubleVar()
            self.tool_dia.set(float(2.333))
 ####################################################################### настройки по дефолту           
            self.depth_D = DoubleVar()
            self.depth_D.set(float(self.parser.get('Parameters','depth_D')))
            
            self.finishing_depth = DoubleVar()
            self.finishing_depth.set(float(self.parser.get('Parameters','finishing_depth')))
                       
            self.feedrate_F = DoubleVar()
            self.feedrate_F.set(float(self.parser.get('Parameters','feedrate_F'))) 
                       
            self.ending_block_Q = DoubleVar()
            self.ending_block_Q.set(float(self.parser.get('Parameters','ending_block_Q')))         
           
            self.start_Z0  = IntVar()
            self.start_Z0.set(float(self.parser.get('Parameters','start_Z0'))) 
            
            self.tool_T  = StringVar()
            self.tool_T.set(self.parser.get('Parameters','tool_T'))
            
            self.reserve_S  = IntVar()
            self.reserve_S.set(float(self.parser.get('Parameters','reserve_S')))
            
            self.reserve_L  = IntVar()
            self.reserve_L.set(float(self.parser.get('Parameters','reserve_L')))            
            
            self.quantity_I  = IntVar()
            self.quantity_I.set(float(self.parser.get('Parameters','quantity_I')))            

            self.tempfile_gcode = self.parser.get('Paths','tempfile_gcode')
            self.editfilename = self.parser.get('Paths','editfilename')
            self.tempfile_rw = self.parser.get('Paths','tempfile_rw')


            
            
            
            
            self.start_rad=DoubleVar()
            self.start_rad.set(float(self.parser.get('Parameters','start_radius')))        
           
            self.axis1_st_en=DoubleVar()
            self.axis1_st_en.set(float(self.parser.get('Plane Coordinates','axis1_start_end')))

            self.axis2_st_en=DoubleVar()
            self.axis2_st_en.set(float(self.parser.get('Plane Coordinates','axis2_start_end')))        
            
            self.axis3_retract=DoubleVar()
            self.axis3_retract.set(float(self.parser.get('Depth Coordinates','axis3_retract')))
            
            self.axis3_safe_margin=DoubleVar()
            self.axis3_safe_margin.set(float(self.parser.get('Depth Coordinates','axis3_safe_margin')))

            self.axis3_slice_depth=DoubleVar()
            self.axis3_slice_depth.set(float(self.parser.get('Depth Coordinates','axis3_slice_depth')))        

            self.axis3_mill_depth=DoubleVar()
            self.axis3_mill_depth.set(float(self.parser.get('Depth Coordinates','axis3_mill_depth')))        
            
            self.F_G1_Depth=DoubleVar()
            self.F_G1_Depth.set(float(self.parser.get('Feed Rates','f_g1_depth')))

            self.F_G1_Plane=DoubleVar()
            self.F_G1_Plane.set(float(self.parser.get('Feed Rates','f_g1_plane')))

            self.points_tolerance=DoubleVar()
            self.points_tolerance.set(float(self.parser.get('Import Parameters','point_tolerance')))

            self.fitting_tolerance=DoubleVar()
            self.fitting_tolerance.set(float(self.parser.get('Import Parameters','fitting_tolerance')))

            self.begin_art=self.parser.get('Route Optimisation', 'Begin art')
            self.max_population=int((int(self.parser.get('Route Optimisation', 'Max. population'))/4)*4)
            self.max_iterations=int(self.parser.get('Route Optimisation', 'Max. iterations'))  
            self.mutate_rate=float(self.parser.get('Route Optimisation', 'Mutation Rate', 0.95))

            self.ax1_letter=self.parser.get('Axis letters', 'ax1_letter')
            self.ax2_letter=self.parser.get('Axis letters', 'ax2_letter')
            self.ax3_letter=self.parser.get('Axis letters', 'ax3_letter')

            self.load_path=self.parser.get('Paths','load_path')
            self.save_path=self.parser.get('Paths','save_path')          

            self.debug=int(self.parser.get('Debug', 'global_debug_level'))

            self.b_D_out = DoubleVar()
            self.b_D_out.set(float(self.parser.get('Parameters','b_D_out')))
            
            self.b_L = DoubleVar()
            self.b_L.set(float(self.parser.get('Parameters','b_L')))            
            
             
            self.b_D_in = DoubleVar()
            self.b_D_in.set(float(self.parser.get('Parameters','b_D_in')))           
                       
            
        except:
            showerror("Error during reading config file", "Please delete or correct\n %s"\
                      %(os.path.join(self.folder,self.cfg_file_name)))
            raise Exception, "Problem during import from INI File" 
            
    def __str__(self):

        str=''
        for section in self.parser.sections(): 
            str= str +"\nSection: "+section 
            for option in self.parser.options(section): 
                str= str+ "\n   -> %s=%s" % (option, self.parser.get(section, option))
        return str

class PostprocessorClass:
    def __init__(self,config=None,textbox=None):
        self.string=''
        self.textbox=textbox
        self.config=config

        self.parser = ConfigParser.ConfigParser()
        self.postpro_file_name=APPNAME+'_postprocessor.cfg'
        self.parser.read(os.path.join(config.folder,self.postpro_file_name))

        if len(self.parser.sections())==0:
            self.make_new_postpro_file()
            self.parser.read(os.path.join(config.folder,self.postpro_file_name))
            textbox.prt(('\nNo postprocessor file found generated new on at: %s' \
                             %os.path.join(config.folder,self.postpro_file_name)))
        else:
            textbox.prt(('\nLoading postprocessor file: %s' \
                             %os.path.join(self.config.folder,self.postpro_file_name)))

        self.get_all_vars()

        textbox.prt(str(self),1)        

    def get_all_vars(self):
        self.abs_export=int(self.parser.get('General', 'abs_export'))
        self.write_to_stdout=int(self.parser.get('General', 'write_to_stdout'))
        self.gcode_be=self.parser.get('General', 'code_begin')
        self.gcode_en=self.parser.get('General', 'code_end')

        self.pre_dec=int(self.parser.get('Number format','pre_decimals'))
        self.post_dec=int(self.parser.get('Number format','post_decimals'))
        self.dec_sep=self.parser.get('Number format','decimal_seperator')
        self.pre_dec_z_pad=int(self.parser.get('Number format','pre_decimal_zero_padding'))
        self.post_dec_z_pad=int(self.parser.get('Number format','post_decimal_zero_padding'))
        self.signed_val=int(self.parser.get('Number format','signed_values'))

        self.use_line_nrs=int(self.parser.get('Line numbers','use_line_nrs'))
        self.line_nrs_begin=int(self.parser.get('Line numbers','line_nrs_begin'))
        self.line_nrs_step=int(self.parser.get('Line numbers','line_nrs_step'))

        self.tool_ch_str=self.parser.get('Program','tool_change')
        self.feed_ch_str=self.parser.get('Program','feed_change')
        self.rap_pos_plane_str=self.parser.get('Program','rap_pos_plane')
        self.rap_pos_depth_str=self.parser.get('Program','rap_pos_depth')
        self.lin_mov_plane_str=self.parser.get('Program','lin_mov_plane')
        self.lin_mov_depth_str=self.parser.get('Program','lin_mov_depth')
        self.arc_int_cw=self.parser.get('Program','arc_int_cw')
        self.arc_int_ccw=self.parser.get('Program','arc_int_ccw')
        self.cut_comp_off_str=self.parser.get('Program','cutter_comp_off')
        self.cut_comp_left_str=self.parser.get('Program','cutter_comp_left')
        self.cut_comp_right_str=self.parser.get('Program','cutter_comp_right')                        
                        
        self.feed=0
        self.x=self.config.axis1_st_en.get()
        self.y=self.config.axis2_st_en.get()
        self.z=self.config.axis3_retract.get()
        self.lx=self.x
        self.ly=self.y
        self.lz=self.z
        self.i=0.0
        self.j=0.0
        if self.diameter_mode():
            self.vars={"%feed":'self.iprint(self.feed)',\
                       "%nl":'self.nlprint()',\
                       "%X":'self.fnprint(self.x)',\
                       "%-X":'self.fnprint(-self.x)',\
                       "%Y":'self.fnprint(self.y*2)',\
                       "%-Y":'self.fnprint(-self.y*2)',\
                       "%Z":'self.fnprint(self.z)',\
                       "%-Z":'self.fnprint(-self.z)',\
                       "%I":'self.fnprint(self.i)',\
                       "%-I":'self.fnprint(-self.i)',\
                       "%J":'self.fnprint(self.j)',\
                       "%-J":'self.fnprint(-self.j)'}
        else:
            self.vars={"%feed":'self.iprint(self.feed)',\
                   "%nl":'self.nlprint()',\
                   "%X":'self.fnprint(self.x)',\
                   "%-X":'self.fnprint(-self.x)',\
                   "%Y":'self.fnprint(self.y)',\
                   "%-Y":'self.fnprint(-self.y)',\
                   "%Z":'self.fnprint(self.z)',\
                   "%-Z":'self.fnprint(-self.z)',\
                   "%I":'self.fnprint(self.i)',\
                   "%-I":'self.fnprint(-self.i)',\
                   "%J":'self.fnprint(self.j)',\
                   "%-J":'self.fnprint(-self.j)'}                   

    def diameter_mode(self):
        self.sgg =("%s\n" %self.gcode_be)
        if re.search("\s*G0?7[^0-9]", self.sgg, re.I):
            return 1
        else:       
            return 0
    def make_new_postpro_file(self):
        pass

    def write_gcode_be(self,ExportParas,load_filename):
        str=("(File: %s)\n" %load_filename)
        self.string=(str.encode("utf-8"))    
        self.string+=("%s\n" %ExportParas.gcode_be.get(1.0,END).strip())

    def write_gcode_en(self,ExportParas):
        self.string+=ExportParas.gcode_en.get(1.0,END)

        self.make_line_numbers()        
        
        return self.string

    def make_line_numbers(self):
        line_format='N%i ' 
        if self.use_line_nrs:
            nr=0
            line_nr=self.line_nrs_begin
            self.string=((line_format+'%s') %(line_nr,self.string))
            nr=self.string.find('\n',nr)
            while not(nr==-1):
                line_nr+=self.line_nrs_step  
                self.string=(('%s'+line_format+'%s') %(self.string[0:nr+1],\
                                          line_nr,\
                                          self.string[nr+1:len(self.string)]))
                
                nr=self.string.find('\n',nr+len(((line_format) %line_nr))+2)
                          
            
            
    def chg_feed_rate(self,feed):
        self.feed=feed
        
    def set_cut_cor(self,cut_cor):
        self.cut_cor=cut_cor

               
    def lin_pol_arc(self,dir,ende,IJ):
        if not(self.abs_export):
            self.x=ende.x-self.lx
            self.y=ende.y-self.lx
            self.lx=ende.x
            self.ly=ende.y
        else:
            self.x=ende.x
            self.y=ende.y

        self.i=IJ.x
        self.j=IJ.y

        if dir=='cw':
            self.string+=self.make_print_str(self.arc_int_cw)
        else:
            self.string+=self.make_print_str(self.arc_int_ccw)

          
    def rap_pos_z(self,z_pos):
        if not(self.abs_export):
            self.z=z_pos-self.lz
            self.lz=z_pos
        else:
            self.z=z_pos

        self.string+=self.make_print_str(self.rap_pos_depth_str)           
         
    def rap_pos_xy(self,newpos):
        if not(self.abs_export):
            self.x=newpos.x-self.lx
            self.lx=newpos.x
            self.y=newpos.y-self.ly
            self.ly=newpos.y
        else:
            self.x=newpos.x
            self.y=newpos.y

        self.string+=self.make_print_str(self.lin_mov_plane_str)        
    
    def lin_pol_z(self,z_pos):
        if not(self.abs_export):
            self.z=z_pos-self.lz
            self.lz=z_pos
        else:
            self.z=z_pos

        self.string+=self.make_print_str(self.lin_mov_depth_str)      
    def lin_pol_xy(self,newpos):
        if not(self.abs_export):
            self.x=newpos.x-self.lx
            self.lx=newpos.x
            self.y=newpos.y-self.ly
            self.ly=newpos.y
        else:
            self.x=newpos.x
            self.y=newpos.y

        self.string+=self.make_print_str(self.lin_mov_plane_str)       

    def make_print_str(self,string):
        new_string=string
        for key_nr in range(len(self.vars.keys())):
            new_string=new_string.replace(self.vars.keys()[key_nr],\
                                          eval(self.vars.values()[key_nr]))
        return new_string

    def iprint(self,interger):
        return ('%i' %interger)

    def nlprint(self):
        return '\n'

    def fnprint(self,number):
        string=''
        if (self.signed_val)and(self.pre_dec_z_pad):
            numstr=(('%+0'+str(self.pre_dec+self.post_dec+1)+\
                     '.'+str(self.post_dec)+'f') %number)
        elif (self.signed_val==0)and(self.pre_dec_z_pad):
            numstr=(('%0'+str(self.pre_dec+self.post_dec+1)+\
                    '.'+str(self.post_dec)+'f') %number)
        elif (self.signed_val)and(self.pre_dec_z_pad==0):
            numstr=(('%+'+str(self.pre_dec+self.post_dec+1)+\
                    '.'+str(self.post_dec)+'f') %number)
        elif (self.signed_val==0)and(self.pre_dec_z_pad==0):
            numstr=(('%'+str(self.pre_dec+self.post_dec+1)+\
                    '.'+str(self.post_dec)+'f') %number)
            
        string+=numstr[0:-(self.post_dec+1)]
        
        string_end=self.dec_sep
        string_end+=numstr[-(self.post_dec):]

        if self.post_dec_z_pad==0:
            while (len(string_end)>0)and((string_end[-1]=='0')or(string_end[-1]==self.dec_sep)):
                string_end=string_end[0:-1]                
        return string+string_end
    
    def __str__(self):

        str=''
        for section in self.parser.sections(): 
            str= str +"\nSection: "+section 
            for option in self.parser.options(section): 
                str= str+ "\n   -> %s=%s" % (option, self.parser.get(section, option))
        return str
        
class Show_About_Info(Toplevel):
    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.transient(parent)

        self.title("About DXF2GCODE")
        self.parent = parent
        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()
        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()
        self.wait_window(self)

    def buttonbox(self):
        box = Frame(self)
        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(padx=5, pady=5)
        self.bind("<Return>", self.ok)
        box.pack()

    def ok(self, event=None):   
        self.withdraw()
        self.update_idletasks()
        self.close()

    def close(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def show_hand_cursor(self,event):
        event.widget.configure(cursor="hand1")
    def show_arrow_cursor(self,event):
        event.widget.configure(cursor="")
        
    def click(self,event):
        w = event.widget
        x, y = event.x, event.y
        tags = w.tag_names("@%d,%d" % (x, y))
        for t in tags:
            if t.startswith("href:"):
                webbrowser.open(t[5:])
                break


    def body(self, master):
        text = Text(master,width=40,height=8)
        text.pack()
        text.tag_config("a", foreground="blue", underline=1)
        text.tag_bind("a", "<Enter>", self.show_hand_cursor)
        text.tag_bind("a", "<Leave>", self.show_arrow_cursor)
        text.tag_bind("a", "<Button-1>", self.click)
        text.config(cursor="arrow")

        href = "https://github.com/nkp2169/G71"
        text.insert(END, "\nVersion Lathe")
        text.insert(END, "\nhttps://github.com/nkp2169/G71", ("a", "href:"+href))


class NotebookClass:    
    def __init__(self, master,width=0,height=0):

        self.active_fr = None
        self.count = 0
        self.choice = IntVar(0)

        self.dummy_x_fr = Frame(master, width=width, borderwidth=0)
        self.dummy_y_fr = Frame(master, height=height, borderwidth=0)
        self.dummy_x_fr.grid(row=0,column=1)
        self.dummy_x_fr.grid_propagate(0)
        self.dummy_y_fr.grid(row=1,rowspan=2,column=0)
        self.dummy_y_fr.grid_propagate(0)

        self.rb_fr = Frame(master, borderwidth=0)
        self.rb_fr.grid(row=1,column=1, sticky=N+W)
        
        self.screen_fr = Frame(master, borderwidth=2, relief=RIDGE)
        self.screen_fr.grid(row=2,column=1,sticky=N+W+E)

        master.rowconfigure(2,weight=1)
        master.columnconfigure(1,weight=1)
        

    def __call__(self):
        return self.screen_fr

    def add_screen(self, fr, title):

        b = Radiobutton(self.rb_fr,bd=1, text=title, indicatoron=0, \
                        variable=self.choice, value=self.count, \
                        command=lambda: self.display(fr))
        
        b.grid(column=self.count,row=0,sticky=N+E+W)
        self.rb_fr.columnconfigure(self.count,weight=1)

        fr.grid(sticky=N+W+E)
        self.screen_fr.columnconfigure(0,weight=1)
        fr.grid_remove()

        if not self.active_fr:
            fr.grid()
            self.active_fr = fr

        self.count += 1

        return b


    def display(self, fr):
        self.active_fr.grid_remove()
        fr.grid()
        self.active_fr = fr


         
class Tkinter_Variable_Dialog(Toplevel):
    def __init__(self, parent=None,title='Test Dialog',label=('label1','label2'),value=(0.0,0.0)):
        if not(len(label)==len(value)):
            raise Exception, "Number of labels different to number of values"

        self.label=label
        self.value=value
        self.result=False

        Toplevel.__init__(self, parent)
        self.transient(parent)

        self.title(title)
        self.parent = parent

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()
        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()
        self.wait_window(self)

    def buttonbox(self):
        
        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def ok(self, event=None):   
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def body(self, master):
        self.tkintervars=[]
        for row_nr in range(len(self.label)):
            self.tkintervars.append(DoubleVar())
            self.tkintervars[-1].set(self.value[row_nr])
            Label(master, text=self.label[row_nr]).grid(row=row_nr,padx=4,sticky=N+W)
            Entry(master,textvariable=self.tkintervars[row_nr],width=10).grid(row=row_nr, column=1,padx=4,sticky=N+W)

    def apply(self):
        self.result=[]
        for tkintervar in self.tkintervars:
            self.result.append(tkintervar.get())

if __name__ == "__main__":
   
    master = Tk()
    master.title("DXF 2 G-Code, Version 0.1")

    if len(sys.argv) > 1:
        Erstelle_Fenster(master,sys.argv[1])
    else:
        Erstelle_Fenster(master)

    master.mainloop()

    

# importations modules and packages 
from openalea.plantgl.all import *
from openalea.caribu.CaribuScene import CaribuScene
import numpy as np
import math

# define function as OOP paradigm


def fonction_triangle_mesh(x,y,ecart_rangee,orientation):
    points =[Vector3(-x/2,-y/2,0),Vector3(x/2,-y/2,0),Vector3(x/2,y/2,0),Vector3(-x/2,y/2,0)]
    sommet=[(0,1,2),(0,2,3)]
    mesh0=TriangleSet(points,sommet)
    rouge = Material(Color3(255,0, 0))
    if orientation in ["est","ouest"]:
        mesh1 = Translated(Vector3(0, -ecart_rangee/4, 0), mesh0)
        mesh2 = Translated(Vector3(0, -ecart_rangee/2, 0), mesh0)
        place_box0 = Shape(mesh0,rouge,id=0)
        place_box1 = Shape(mesh1,rouge,id=1)
        place_box2 = Shape(mesh2,rouge,id=2)
        
    else:
        mesh1 = Translated(Vector3(-ecart_rangee/4, 0, 0), mesh0)
        mesh2 = Translated(Vector3(-ecart_rangee/2,0 , 0), mesh0)
        place_box0 = Shape(mesh0,rouge,id=0)
        place_box1 = Shape(mesh1,rouge,id=1)
        place_box2 = Shape(mesh2,rouge,id=2)
    scene_final=Scene([place_box0,place_box1,place_box2])
    return scene_final

class geometry_panel:
    # default values ==1 for creating object panel
    
    def __init__(self,height_p=1,length_p=1,width_p=1,nb_arrow=1,nb_panel=1,panel_dist=1,arrow_dist=1):
        # to get dimensions caracteristiks
        self.height_p=height_p
        self.length_p=length_p
        self.width_p=width_p
        self.nb_arrow=nb_arrow
        self.nb_panel=nb_panel
        self.panel_dist=panel_dist
        self.arrow_dist=arrow_dist

class Fixed_panel_scene:
    """
    meth: Construct_panel 
    meth: Construct_soil
    
    """
    def __init__(self,geometry_panel,orientation="sud",type_panel="normal",opacity=1):
        self.orientation=orientation
        self.type=type_panel
        self.opacity=opacity
        self.geometry_panel=geometry_panel
    # this method is used to create panel mock-up 
        """the input is dicctionnary that contains 
        orientation,type_panneau,longeur_p,largeur_pnnb_panel,nb_rangee,ecart_panel,ecart_rangee,
        hauteur_haut_p,hauteur_p_bas,angle_p,panel_opacity
        """
    def Panel_scene(self,params):
        # extraction dictionnary
        keys=["orientation","type_panneau","longueur_p","largeur_p","nb_panel","nb_rangee","hauteur_haut_p",
                    "hauteur_bas_p","angle_p","panel_opacity","ecart_panel","ecart_rangee"]
        
        (orientation,type_panneau,longueur_p,largeur_p,nb_panel,nb_rangee,hauteur_haut_p,
                    hauteur_bas_p,angle_p,panel_opacity,ecart_panel,ecart_rangee)=map(params.get,keys)
        
        angle_rad = math.radians(angle_p)
        hauteur_p = (hauteur_haut_p + hauteur_bas_p) / 2
        panel_final = []
        panel_unit = Box(Vector3(longueur_p/2, largeur_p/2, 0.001))
        poteau_init=[Cylinder(radius=0.05,height=hauteur_p)]
        pot_final=[]
        
        # when the panel is normal we use one rectangle to represent panel surface
        
        if type_panneau == "normal":
            panel_base = AxisRotated(Vector3(1,0,0), angle_rad, panel_unit)
            panel_incl = Translated(Vector3(0,0,hauteur_p), panel_base)
            panel_final_shape = [panel_incl]
            
        # when the panel is chapeau (hat) then we had two surfaces panels for representing geometry
        else:
            panel_base = Translated(Vector3(0,-largeur_p/2,0), panel_unit)
            panel_inc = AxisRotated(Vector3(1,0,0), angle_rad, panel_base)

        # first side of panel 
            panel_1 = Translated(Vector3(0,0,hauteur_p), panel_inc) 
            
        # the second side of panel
            panel_2 = AxisRotated(Vector3(0,0,1), math.pi, panel_1)
            panel_final_shape = [panel_1, panel_2]

        # to get the exact panel orientation for caribu simulation 
        """
        there is a sight difference between plantgl orientation and caribuscene orientation
        for corresponding between plantgl and caribuscene orientation, here is some important 
        information : plantgl -X is the south caribuscene 
        plantgl X is the north caribuscene 
        plantgl-Y is the east caribuscene and plantglY is the west 
        Returns:
            Due to the fact that we are build or geometry on plantgl, the following mapping function 
            was setting to set up the exact orientation based on Caribuscene orientation build on 
            plantgl
        """
        mapping = {
            "sud": -math.pi/2, #
            "nord": math.pi/2,
            "est": 0,
            "ouest": math.pi}
        
        angle_orientation = mapping.get(orientation, 0)

        """
        the purpose of this function is to simulate light shelterring with at least 4 panels arrows
        and 4 panels. for this purpose, we are going to centralize (0,0,0) the scene, that is why
        we set offset x and y according to number of panel array and panel unit number
        """
        
        offset_y_global = -((nb_rangee - 1) * (ecart_rangee)) / 2
        offset_x_global = -((nb_panel - 1) * ( ecart_panel)) / 2
        
        id_p=3000000 # id panel that was choosed arbirtraily 
        
        for rang in range(nb_rangee):
            for pan in range(nb_panel):
                y = offset_y_global + rang * (ecart_rangee)
                x = offset_x_global + pan * (ecart_panel)

                # matrice rotation 
                x_rot = x * math.cos(angle_orientation) - y * math.sin(angle_orientation)
                y_rot = x * math.sin(angle_orientation) + y * math.cos(angle_orientation)

                for p in panel_final_shape:
                    p_rot = AxisRotated(Vector3(0,0,1), angle_orientation, p)
                    p_trans = Translated(Vector3(x_rot, y_rot, 0), p_rot)
                    panel_final.append(Shape(p_trans,id=id_p))
                    
                # we can also add the panel post
                for pot in poteau_init:
                    pot_int=Translated(Vector3(x_rot,y_rot, 0),pot)
                    pot_final.append(pot_int)
                
        panel_colore = [Shape(panel.geometry, Material(Color3(58,56,56)),id=panel.id)for panel in panel_final]
        poteau_colore=[Shape(pot_1,Material(Color3(58,56,56))) for pot_1 in pot_final]
        return Scene(panel_colore),poteau_colore
    
    def Soil_scene(self,ecart_p,ecart_rang,long_x_p,larg_y_p,orientation="sud",resol=0.01):
        """_summary_
        Args:
            ecart_p (_type_): _panle ecart_
            ecart_rang (_type_): _rang distance_
            long_x_p (_type_): _panel length_
            larg_y_p (_type_): _panel width_
            orientation (str, optional): _description_. Defaults to "sud".
            resol (float, optional): _description_. Defaults to 0.01.
        Returns:
            _type_: _description_
        """
        resol_x=resol
        resol_y=resol
        points =[Vector3(-resol_x/2,-resol_y/2,0),Vector3(resol_x/2,-resol_y/2,0),Vector3(resol_x/2,resol_y/2,0),Vector3(-resol_x/2,resol_y/2,0)]
        sommet=[(0,1,2),(0,2,3)]
        triangle_unit=TriangleSet(points,sommet)
        
        if orientation =="sud":
            nb_pixel_x= math.ceil((ecart_rang+larg_y_p)/resol)
            nb_pixel_y= math.ceil((ecart_p + long_x_p)/resol)

        else:
            nb_pixel_x=math.ceil((ecart_p + long_x_p)/resol)
            nb_pixel_y=math.ceil((ecart_rang + larg_y_p)/resol)
        # central mesh
        pos_x_depart=-(nb_pixel_x-1)*resol_x/2
        pos_y_depart=-(nb_pixel_y-1)*resol_y/2
        id_sol=0
        maillage=[]
        for i in range(nb_pixel_x):
            for j in range(nb_pixel_y):
                x_final = pos_x_depart + (resol_x * i)
                y_final = pos_y_depart + (resol_y * j)
                objet=Shape(Translated(Vector3(x_final,y_final,0),triangle_unit),id=id_sol)
                maillage.append(objet)
                id_sol+=1
        maillage_col=[Shape(maille.geometry, Material(Color3(255,255,255)), id=maille.id) for maille in maillage]
        return Scene(maillage_col)
   
   
   
    
class Mobile_panel_scene:
    
    def __init__(self,height_p=1,length_p=1,width_p=1,nb_arrow=1,nb_panel=1,panel_dist=1,arrow_dist=1):
        # to get dimensions caracteristiks
        self.height_p=height_p
        self.length_p=length_p
        self.width_p=width_p
        self.nb_arrow=nb_arrow
        self.nb_panel=nb_panel
        self.panel_dist=panel_dist
        self.arrow_dist=arrow_dist
    
    def type_panneau_orient_st(self,orientation,longueur_p,largeur_p,nb_panel,nb_rangee,ecart_panel,ecart_rangee,hauteur_p,angle_p):
        """
        largeur_p= distance in y coordonate (row line)
        longeur_p= distance in x coordonate (range line)
        orientation = where the panel facing (north,south, east and west)
        hauteur_p: the elevation when the panel is set plate (0)
        
        #### function solar tracking and antitracking
        alpha_s = sunelevation angle
        beta_s = sun angle azimutal 
        alpha_p= panel angle azimutal
        beta_p = the optimum angle for solar or anti tracking
         """
        #### creation unit panel inclinate
        angle_rad=angle_p
        ##
        panel_final = []
        panel_unit = Box(Vector3(longueur_p/2, largeur_p/2, 0.001))
        # panel_incl = AxisRotated(Vector3(1,0,0), angle_rad, panel_unit)
        # panel_base = Translated(Vector3(0,0,hauteur_p), panel_incl)
        
        panel_incl = Translated(Vector3(0,0,hauteur_p), panel_unit)
        panel_base = AxisRotated(Vector3(1,0,0), angle_rad, panel_incl)
        
        poteau_init=[Cylinder(radius=0.05,height=hauteur_p)]
        panel_final_shape = [panel_base]
        pot_final=[]
        
        mapping = {
            "sud": -math.pi/2,
            "nord": math.pi/2,
            "est": 0,
            "ouest": math.pi}
        angle_orientation = mapping.get(orientation, 0)

        offset_y_global = -((nb_rangee - 1) * (ecart_rangee)) / 2
        offset_x_global = -((nb_panel - 1) * ( ecart_panel)) / 2
        id_p=3000000
        for rang in range(nb_rangee):
            for pan in range(nb_panel):
                y = offset_y_global + rang * (ecart_rangee)
                x = offset_x_global + pan * (ecart_panel)

                x_rot = x * math.cos(angle_orientation) - y * math.sin(angle_orientation)
                y_rot = x * math.sin(angle_orientation) + y * math.cos(angle_orientation)

                for p in panel_final_shape:
                    p_rot = AxisRotated(Vector3(0,0,1), angle_orientation, p)
                    p_trans = Translated(Vector3(x_rot, y_rot, 0), p_rot)
                    panel_final.append(Shape(p_trans,id=id_p))
                    
                for pot in poteau_init:
                    pot_int=Translated(Vector3(x_rot,y_rot, 0),pot)
                    pot_final.append(pot_int)
                    
        panel_colore = [Shape(panel.geometry, Material(Color3(58,56,56)),id=panel.id)for panel in panel_final]
        poteau_colore=[Shape(pot_1,Material(Color3(58,56,56))) for pot_1 in pot_final]
        return Scene(panel_colore),poteau_colore
    
    ### function between angle panel and solar position
    # first one used to figure out the betap of antitracking
    """
    for the solar tracking, the equation was derived and the angle beta was obtain when the 
    derived equation were set to equal zero
    the angle is between [-pi/2 and pi/2] pi/2 earlier in the morning and -pi/2 before the sun goes down

    for the antitracking, we simply solve the main fonction to equal zero

    """
    
    def fonction_A_betap(self,alpha_s,beta_s,beta_p,alpha_p=0):
        return np.cos(beta_p)*((np.sin(alpha_s)*np.sin(beta_s)*np.sin(alpha_p)+np.cos(alpha_s)*np.cos(beta_s)*np.cos(alpha_p)))

    def fonction_B_beta_p(self,beta_s,beta_p):
        return np.sin(beta_p)*(np.sin(beta_s))

    ## important for solving the equation 
    def fonction_X(self,alpha_s,beta_s,alpha_p=0):
        return np.sin(alpha_s)*np.sin(beta_s)*np.sin(alpha_p)+np.cos(alpha_s)*np.cos(beta_s)*np.cos(alpha_p)
    
    def fonction_Y (self,beta_s):
        return np.sin(beta_s)
        ## fonctions derivée use to determine the angle beta_p solar tracking
    def fonction_A_beta_p_prime(self,alpha_s,beta_s,beta_p,alpha_p=0):
        -np.sin(beta_p)*((np.sin(alpha_s)*np.sin(beta_s)*np.sin(alpha_p)+np.cos(alpha_s)*np.cos(beta_s)*np.cos(alpha_p)))
        
    def fonction_B_beta_p_prime(self,beta_s,beta_p):
        return np.cos(beta_p)*(np.sin(beta_s))
    

scene=Scene(r"SIGNAUX\BGEOM_SIGNAL_SIMULATION\BGEOM_POSTERS\RED_FARED_PLOTLD1_P_SUD.bgeom")
Viewer.display(scene)

    
    
        
        
    

      
    

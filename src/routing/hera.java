/*
 * Copyright 2010 Aalto University, ComNet
 * Released under GPLv3. See LICENSE.txt for details. 
 */
package routing;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import routin.util.RoutingInfo;

import util.Turple;

import core.Connection;
import core.DTNHost;
import core.Message;
import core.Settings;
import core.SimClock;

/**
 * Implementation of the Hop Expansion Routing Algorithm (HERA) as described in 
 * <I>Paper Name Here</I> by
 */
public class HeraRouter extends ActiveRouter {
    /** Constants Need to go here */
    /** local transitivity trust scaling constants, default values */
    public static final double[] DEFAULT_LAMBDA = {1, .5, .05, .005, .0005};
    /** size of Lambda array */
    public static final int DEFAULT_LAMBDA_SIZE = 5;
    /** global trust scaling constants, default values */
    public static final double[] DEFAULT_GAMMA = {1, .5, .05, .005, .0005};
    /** size of Gamma array */
    public static final int DEFAULT_GAMMA_SIZE = 5;
    /** delivery reachability aging constant */
    public static final double DEFAULT_ALPHA = 0.98;

    /** Namespaces here & Settings file strings*/
    /** Hera router's setting namespace ({@value})*/
    public static final String HERA_NS = "HeraRouter";
    /**
     * Number of seconds in time unit -setting id ({@value}).
     * How many seconds one time unit is when calculating aging of
     * delivery predictions. Should be tweaked for the scenario.*/
    public static final String SECONDS_IN_UNIT_S = "secondsInTimeUnit";
    /** Hop transitivity scaling constants (lambda) -setting id ({@value}).
     * Default values for the setting in {@link #DEFAULT_LAMBDA}.
     */
    public static final String LAMBDA_S = "lambda";
    /** Size of the array that defines lambda -setting id ({@value}).
     * Default values for the setting in {@link #DEFAULT_LAMBDA_SIZE 
     */
    public static final String SIZEOF_LAMBDA_S = "sizeOfLambda";
    /** Hop comparison function scaling constants (gamma) -setting id
     * ({@value}).
     * default values for the setting in {@link #DEFAULT_GAMMA}.
     */
    public static final String GAMMA_S = "gamma";
    /** Size of the array that defines gamma -setting id ({@value}).
     * Default values for the setting in {@link #DEFAULT_GAMMA_SIZE
     */
    public static final String SIZEOF_GAMMA_S = "sizeOfGamma";
    /** aging constant (alpha) -setting id ({@value}).
     * default value for the setting in {@link #DEFAULT_ALPHA}.
     */
    public static final String ALPHA_S = "alpha";
    
    /** private variables holding above referenced values */
    /** the value of nrof seconds in time unit -setting */
    private int secondsInTimeUnit;
    /** value of lambda setting */
    private double[] lambda;
    /** size of lambda array */
    private int sizeofLambda;
    /** values of gamma setting */
    private double[] gamma;
    /** size of gamma array */
    private int sizeofGamma;
    /** aging constant */
    private double alpha;
    /** delivery reachability value.
     * data struct holding the M matrix values 
     */
    private Map<DTNHost, Map<Integer, Double>> reach;
    /** last delivery reachability update (sim) time */
    private double lastAgeUpdate;

    /**
     * Constructor. Creates a new message router based on the settings in 
     * the given settings object.
     * @param s the settings object
     */
    public HeraRouter(Settings s) {
        super(s);
        Settings heraSettings = new Settings(HERA_NS);
        secondsInTimeUnit = heraSettings.getInt(SECONDS_IN_UNIT_S);

        // checking for HeraRouter.lambda = x, y, z
        // Also checks for nrofLambda values. Need both
        if (heraSettings.contains(SIZEOF_LAMBDA_S) &&
            heraSettings.contains(LAMBDA_S)) {
            
            // use custom sizeofLambda setting
            sizeofLambda = heraSettings.getInt(SIZEOF_LAMBDA_S);
            // use custom set of lambda values
            lambda = heraSettings.getCsvDoubles(LAMBDA_S, sizeofLambda);
        } else{
            // use default values for both size & values if either fails
            sizeofLambda = DEFAULT_LAMBDA_SIZE;
            lambda = DEFAULT_LAMBDA;
        }

        // check for HeraRouter.gamma & HeraRouter.sizeofGamma
        if (heraSettings.contains(SIZEOF_GAMMA_S) && 
            heraSettings.contains(GAMMA_S)) {
            
            // use custom gamma settings from settings file
            sizeofGamma = heraSettigns.getInt(SIZEOF_GAMMA_S);
            gamma = heraSettings.getCsvDoubles(GAMMA_S, sizeofGamma);
        } else{
            // use default values for gamma related vars
            sizeofGamma = DEFAULT_GAMMA_SIZE;
            gamma = DEFAULT_GAMMA;
        }

        // check for the aging constant in settings file
        // if none, the default value of 0.98 will be used
        if (heraSettings.contains(ALPHA_S) {
            alpha = heraSettings.getDouble(ALPHA_S);
        } else{
            alpha = DEFAULT_ALPHA;
        }
        
        // initialize the M matrix data structure
        initReach();
    }
    
    /**
     * Copy constructor.
     * @param r The router prototype where settings values are copied from
     */
    protected HeraRouter(HeraRouter r) {
        super(r);
        this.secondsInTimeUnit = r.secondsInTimeUnit;
        this.alpha = r.alpha;
        this.sizeofLambda = r.sizeofLambda;
        this.sizeofGamma = r.sizeofGamma;
        this.lambda = r.lambda;
        this.gamma = r.gamma;
        initReach();
    }

    /**
     * Initialize reachability map of map structure
     * this is the M matrix described in paper
     */
    private void initReach(){
        this.reach = new HashMap<DTNHost, Map<Integer, Double>>();
    }

    // need to update this for hera
    @Override
    public void changedCOnnection(Connection con) {
        super.changedConnection(con);

        if (con.isUp()) {
            DTNHost otherHost = con.getOtherNode(getHost());
            updateReachFor(otherHost);
            updateHopReach(otherHost);
        }
    }

    /** 
     * Update the 0-lvl hop value, Direct hop metric value
     * <CODE>M(0, (A,B))_new = M(0, (A,B))_old + 1</CODE>
     * @param host The host just met
     */
    private void updateReachFor(DTNHost host){
         
    }

} // Bracket end for whole class 

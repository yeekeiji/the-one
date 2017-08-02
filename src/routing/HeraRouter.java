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

import routing.util.RoutingInfo;

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
    /** size of all system pertinent arrays 
     * both gamma and lambda arrays need to match this size
     */
    public static final int DEFAULT_SYS_SIZE = 5;
    /** global trust scaling constants, default values */
    public static final double[] DEFAULT_GAMMA = {1, .5, .05, .005, .0005};
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
    public static final String SIZEOF_SYS_S = "sizeOfSys";
    /** Hop comparison function scaling constants (gamma) -setting id
     * ({@value}).
     * default values for the setting in {@link #DEFAULT_GAMMA}.
     */
    public static final String GAMMA_S = "gamma";
    /** aging constant (alpha) -setting id ({@value}).
     * default value for the setting in {@link #DEFAULT_ALPHA}.
     */
    public static final String ALPHA_S = "alpha";
    
    /** private variables holding above referenced values */
    /** the value of nrof seconds in time unit -setting */
    private int secondsInTimeUnit;
    /** value of lambda setting */
    private double[] lambda;
    /** size of lambda and gamma arrays */
    private int sizeofSys;
    /** values of gamma setting */
    private double[] gamma;
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
        if (heraSettings.contains(SIZEOF_SYS_S) &&
            heraSettings.contains(LAMBDA_S)) {
            // use custom sizeofSys setting
            sizeofSys = heraSettings.getInt(SIZEOF_SYS_S);
            // use custom set of lambda values
            lambda = heraSettings.getCsvDoubles(LAMBDA_S, sizeofSys);
        } else{
            // use default values for both size & values if either fails
            sizeofSys = DEFAULT_SYS_SIZE;
            lambda = DEFAULT_LAMBDA;
        }

        // check for HeraRouter.gamma & HeraRouter.sizeofGamma
        if (heraSettings.contains(SIZEOF_SYS_S) && 
            heraSettings.contains(GAMMA_S)) {
            // use custom gamma settings from settings file
            gamma = heraSettings.getCsvDoubles(GAMMA_S, sizeofSys);
        } else{
            // use default values for gamma related vars
            gamma = DEFAULT_GAMMA;
        }

        // check for the aging constant in settings file
        // if none, the default value of 0.98 will be used
        if (heraSettings.contains(ALPHA_S)) {
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
        this.sizeofSys = r.sizeofSys;
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
            updateTransitiveReach(otherHost);
        }
    }

    /** 
     * Update the 0-lvl hop value, Direct hop metric value
     * <CODE>M(0, (A,B))_new = M(0, (A,B))_old + 1</CODE>
     * @param host The host just met
     */
    private void updateReachFor(DTNHost host){
        int DIRECT_HOP = 0;

        // 0 input b/c we are updating the direct encounter metric value
        double oldValue = getReachFor(host, DIRECT_HOP);

        double updateValue = oldValue + lambda[DIRECT_HOP];

        // the +1 (DEFAULT VALUE) is the abs trust in a direct meeting
        reach.get(host).replace(DIRECT_HOP, updateValue); 
    }

    /**
     * Return the current reachability value for a host's spec hop
     * if M(h, (A, i) ) dne, add all values to the reach & init to 0
     */
    public double getReachFor(DTNHost host, int hopLvl){
        // age reach values if they exist
        ageReachVals();

        // host exists in reach case
        if (!reach.containsKey(host)){
            Map<Integer, Double> temp = new HashMap<Integer, Double>();

            // initial reach value for all hop levels
            double INIT_VALUE = 0.0;

            // create an all zero dict for m_i values of "host"
            for(int i = 0; i < this.sizeofSys; ++i){
                temp.put(i, INIT_VALUE); 
            }
            // add host w/ all 0 m_i values 
            this.reach.put(host, temp);
        }
        
        // returns the VALUE of (host) : (hop level):VALUE
        // inside of reach
        return this.reach.get(host).get(hopLvl);
    }

    /**
     * Update transitive (A->B->C) hop reachability
     * <CODE>M(h, (A,i))_new = M(h, (A,i))_old + lambda[h] * M(h-1, (B,i))_old
     * </CODE>
     * @param host the host we just met
     */
    private void updateTransitiveReach(DTNHost host){
        MessageRouter otherRouter = host.getRouter();
        assert otherRouter instanceof HeraRouter : "Hera only works " +
            " with other routers of the same type";

        // age reach values before doing any updates
        ageReachVals();
        Map<DTNHost, Map<Integer, Double>> othersReach = 
            ((HeraRouter)otherRouter).getReach();

        for (Map.Entry<DTNHost, Map<Integer, Double>> e : othersReach.entrySet()){
            
            // skip node A whose calling the transitivity update. 
            // irrelevant to update A's reach to A
            if (e.getKey() == getHost()){
                continue;
            }
            
            // init map values for host reach has never seen to all 0 values
            if ( !reach.containsKey( e.getKey() ) ){
                Map<Integer, Double> newHost = new HashMap<Integer, Double>();
                for( int i = 0; i < this.sizeofSys; ++i){
                    newHost.put(i, 0.0);
                }
                this.reach.put(e.getHost(), newHost);
            }
                // update transitive hop values for h = 1,...,H
                for( int h = 1; h < this.sizeofSys; ++h){
                    // delta = how much you are changing old value by
                    double delta = lambda[h] * otherReach.get(e.getKey()).get(h - 1);
                    double rNew = this.reach.get(e.getKey()).get(h) + delta;
                    this.reach.get(e.getKey()).put(h, rNew);
                }
        }
    }

    /**
     * Ages all entries in the map of maps, reach
     * <CODE>M(h, (A,i))_new = M(h, (A,i))_old * (ALPHA ^ K)</CODE), where k 
     * is the number of time units that have elapsed since the last time the
     * metric was aged.
     * @see #SECONDS_IN_UNIT_S
     */
    private void ageReachVals() {
        double timeDiff = (SimClock.getTime() - this.lastAgeUpdate) /
            secondsInTimeUnit;

        if (timeDiff == 0) {
            return;
        }

        double mult = Math.pow(alpha, timeDiff);

        // age each host in reach map of maps 
        for (Map.Entry<DTNHost, Map<Integer, Double>> e : this.reach.entrySet()){
            // age each hop lvl for h = 0,...,H
            for ( int h = 0; h < sizeofSys; ++h ) {
                double agedVal = this.reach.get(e.getKey()).get(h) * mult;
                this.reach.get(e.getKey()).put(h, agedVal);
            }
        }
        // update the time that you aged the reach map of maps
        this.lastAgeUpdate = SimClock.getTime();
    }

    /**
     * Returns the reach matrix of this router's reachability
     * @return the reach matrix map of maps for this router's reach attribute
     */
    private Map<DTNHost, Map<Integer, Double>> getReach() {
        ageReachVals();
        return this.reach;
    }

    // 7/31/17 1:45PM same as prophet ver 
    @Override
    public void update() {
        super.update();
        if ( !canStartTransfer() || isTransfering() ) {
            return; // nothing to transfer or currently transfering.
        }

        // try messages that could be delivered to final recipient
        if ( exchangeDeliverableMessage() != null) {
            return;
        }

        tryOtherMessages();
    }

// fix the line with comparison of getPredFor, replace with omega calcs
    /**
     * Tries to send all other messages to all connected hosts ordered by
     * their hop metrics 
     * @return The return value of {@link #tryMessagesForConnected(List)}
     */
    private Turple<Message, Connection> tryOtherMessages() {
        List<Turple<Message, Connection>> messages =
            new ArrayList<Turple<Message, Connection>>();

        Collection<Message> msgCollection = getMessageCollection();

        /* for all connected hosts collect all messages that have a higher
         * reach metric value (omega var in paper) than the other host */
        for ( Connection con : getConnections() ) {
            DTNHost other = con.getOtherNode(getHost());
            HeraRouter othRouter = (HeraRouter)other.getRouter();

            if (othRouter.isTransfering()) {
                continue; // skip hosts that are transferring
            }

            for ( Message m : msgCollection ) {
                if ( othRouter.hasMessage(m.getId())) {
                    continue; // skip messages that other one has
                }
                // change this check later. Need to use omega comparison
                if (othrouter.omega(m.getTo()) > this.omega(m.getTo())) {
                // the other node has larger reach and possibility of delivery
                messages.add(new Turple<Message, Connection>(m,con));
                }
            }
        }

        if (messages.size() == 0) {
            return null;
        }

        // sort the message-connection tuples
        Collections.sort(messages, new TupleComparator());
        return tryMessagesForConnected(messages); // try to send messages
    }

    /**
     * Decision function Omega that takes the inner product of M[:, E]_A
     * where A = node calling the function, E = the end node you want to know
     * the reachability metric value of
     * calcs gamma * ( M[:,E]_A ), note gamma = row vector & M[:,E]_A column
     * vector
     * @param host the destination host, Omega(A, host)
     * @return reachability double value representing the likelihood that node A
     * will reach node host
     */
    double omega(DTNHost host){
        ageReachVals();

        // grab the map of values for the input host, 
        // equv to grabbing column of matrix
        Map<Integer, Double> hopMetric = this.reach.get(host);
        double reachability = 0;

        // calculating the inner product
        for (int h = 0; h < this.sizeofSys; ++h){
            double elementMult = gamma[h] * hopMetric.get(h);
            reachability += elementMult;
        }

        return reachability;
    }

    // Need to fix this to work with HERA, verify, possibly fixed
    /**
     * Comparator for Message-Connection-Turples that order the turples by
     * their hop metric by the host on the other side of the connection
     * (GRTRMAX)
     */
    private class TupleComaparator implements Comparator
        <Tuple<Message, Connection>> {

        public int compare(Tuple<Message, Connection> tuple1, 
            Tuple<Message, Connection> tuple2) {
            // hop metric of turple1's message with turple1's connection
            double r1 = ((HeraRouter)tuple1.getValue().
                    getOtherNode(getHost()).getRouter()).omega(
                    tuple1.getKey().getTo());

            double r2 = ((HeraRouter)tuple2.getValue().
                    getOtherNode(getHost()).getRouter()).omega(
                    tuple2.getKey().getTo());
             

             // bigger value should come first ? 
             if ( r2 - r1 == 0 ) {
                /* equal probabilities -> let queue mode decide */
                return compareByQueueMode(tuple1.getKey(), tuple2.getKey());
            } else if (r2 - r1 < 0) {
                return -1;
            } else {
                return 1;
            }
        }
    }

    // change to be compliant with HERA's multi-level values 
    // Q: what is RoutingInfo? check parent classes 
    @Override
    public RoutingInfo getRoutingInfo() {
        ageReachVals();
        RoutingInfo top = super.getRoutingInfo();
        RoutingInfo ri = new RoutingInfo(reach.size() + 
            " delivery predictions(s)");

        for (Map.Entry<DTNHost, Map<Integer,Double>> e : reach.entrySet()) {
            DTNHost host = e.getKey();
            Double value = omega(host);

            ri.addMoreInfo(new RoutingInfo(String.format("%s : %.6f", 
                    host, value)));
        }

        top.addMoreInfo(ri);
        return top;
    }

    @Override
    public MessageRouter replicate() {
        HeraRouter r = new HeraRouter(this);
        return r;
    }

             
} // Bracket end for whole class 

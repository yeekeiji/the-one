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

import util.Tuple;

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
    public static final int DEFAULT_HOPS_SIZE = 5;
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
    public static final String HOPS_S = "hops";
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
    private int hops;
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
        if (heraSettings.contains(HOPS_S) &&
                heraSettings.contains(LAMBDA_S)) {
            // use custom hops setting
            hops = heraSettings.getInt(HOPS_S);
            // use custom set of lambda values
            lambda = heraSettings.getCsvDoubles(LAMBDA_S, hops);
        } else{
            // use default values for both size & values if either fails
            hops = DEFAULT_HOPS_SIZE;
            lambda = DEFAULT_LAMBDA;
        }

        // check for HeraRouter.gamma & HeraRouter.sizeofGamma
        if (heraSettings.contains(HOPS_S) && 
                heraSettings.contains(GAMMA_S)) {
            // use custom gamma settings from settings file
            gamma = heraSettings.getCsvDoubles(GAMMA_S, hops);
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
        this.hops = r.hops;
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

    @Override
    public void changedConnection(Connection con) {
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

        if(!reach.containsKey(host)){
            Map<Integer, Double> newHost = new HashMap<Integer, Double>();
            
            // initial reach value for all hop levels
            double INIT_VALUE = 0.0;

            // direct hop calculation
            // m_new = m_old + lambda[0]
            // m_old = 0 in this case
            newHost.put(DIRECT_HOP, this.lambda[0]);

            // create an all zero map for m_i values of "host"
            for(int i = 1; i < this.hops; ++i){
                newHost.put(i, INIT_VALUE); 
            }
            // add host w/ all 0 m_i values 
            this.reach.put(host, newHost);
        }

        // 0 input b/c we are updating the direct encounter metric value
        double oldValue = getReachFor(host, DIRECT_HOP);

        double updateValue = oldValue + lambda[DIRECT_HOP];

        // the +1 (DEFAULT VALUE) is the abs trust in a direct meeting
        this.reach.get(host).put(DIRECT_HOP, updateValue); 
    }

    /**
     * Return the current reachability map for a specific host's
     * if M(h, (A, i) ) dne, add all values to the reach & init to 0
     */
    public Map<Integer, Double> getReachFor(DTNHost host){
        // age reach values if they exist
        ageReachVals();

        // return the corresponding map to input Host 
        // return inner_map of reach = (host : inner_map(int : double))
        return this.reach.get(host);
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
            return 0.0;
        } else {
            // returns double inside reach for a specific host's hoplvl
            // similar to reach[host][hoplvl] if this were a 2d array
            return this.reach.get(host).get(hopLvl);
        }
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
            
            // if reach hasn't seen host before, init an all 0 hop metric map
            // e.g. { host: {0: 0.0, 1: 0.0, 2: 0.0...,H: 0.0} }
            if ( !reach.containsKey( e.getKey() ) ){
                double INIT_VAL = 0.0;
                Map<Integer, Double> newHost = new HashMap<Integer, Double>();
                for( int i = 0; i < this.hops; ++i){
                    newHost.put(i, INIT_VAL);
                }
                this.reach.put(e.getKey(), newHost);
            }

            // update transitive hop values for h = 1,...,H
            for( int h = 1; h < this.hops; ++h){
                // delta = how much you are changing old value by
                double delta = lambda[h] * othersReach.get(e.getKey()).get(h - 1);
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
            for ( int h = 0; h < hops; ++h ) {
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

    @Override
    public void update() {
        super.update();
        if ( !canStartTransfer() || isTransferring() ) {
            return; // nothing to transfer or currently transferring.
        }

        // try messages that could be delivered to final recipient
        if ( exchangeDeliverableMessages() != null) {
            return;
        }

        tryOtherMessages();
    }

    /**
     * Tries to send all other messages to all connected hosts ordered by
     * their hop metrics 
     * @return The return value of {@link #tryMessagesForConnected(List)}
     */
    private Tuple<Message, Connection> tryOtherMessages() {
        List<Tuple<Message, Connection>> messages =
            new ArrayList<Tuple<Message, Connection>>();

        Collection<Message> msgCollection = getMessageCollection();

        /* for all connected hosts collect all messages that have a higher
         * reach metric value (omega var in paper) than the other host */
        for ( Connection con : getConnections() ) {
            DTNHost other = con.getOtherNode( getHost() );
            HeraRouter othRouter = ( HeraRouter )other.getRouter();

            if (othRouter.isTransferring()) {
                continue; // skip hosts that are transferring
            }

            for ( Message m : msgCollection ) {
                if ( othRouter.hasMessage( m.getId() ) ) {
                    continue; // skip messages that other one has
                }
                if (othRouter.omega(m.getTo()) > this.omega(m.getTo())) {
                // the other node has larger reach and possibility of delivery
                messages.add(new Tuple<Message, Connection>(m,con));
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
     * will reach node "host"
     */
    public double omega(DTNHost host){
        ageReachVals();

        // handle's case where host is not tracked
        if (!(this.reach.containsKey(host))){
            return 0;
        } else {

            // grab the map of values for the input host, 
            // equivalent to grabbing column of matrix
            Map<Integer, Double> hopMetric = this.getReachFor(host);
            double reachability = 0;

            // calculating the inner product
            for (int h = 0; h < this.hops; ++h){
                double elementMult = this.gamma[h] * this.reach.get(host).get(h);
                reachability += elementMult;
            }
            return reachability;
        }
    }

    /**
     * Comparator for Message-Connection-Tuples that order the tuples by
     * their hop metric by the host on the other side of the connection
     * (GRTRMAX)
     */
    private class TupleComparator implements Comparator
        <Tuple<Message, Connection>> {

        public int compare(Tuple<Message, Connection> tuple1, 
            Tuple<Message, Connection> tuple2) {
            // hop metric of tuple1's message with tuple1's connection
            double r1 = ((HeraRouter)tuple1.getValue().
                    getOtherNode(getHost()).getRouter()).omega(
                    tuple1.getKey().getTo());

            // hop metric of tuple2's message with tuple2's connection
            double r2 = ((HeraRouter)tuple2.getValue().
                    getOtherNode(getHost()).getRouter()).omega(
                    tuple2.getKey().getTo());
             

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

             
} 

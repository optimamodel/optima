ALL_PARAMETERS_SOURCE = \
"""
No.;Parameter name;Location;Model variable name;Data variable name;Manual calibration?;Programs/scenarios?;By population?
1;Condoms | Proportion of sexual acts in which condoms are used with commercial partners;Programs/scenarios;M.condom.com[:];sex.condomcom;;1;1
2;Condoms | Proportion of sexual acts in which condoms are used with casual partners;Programs/scenarios;M.condom.cas[:];sex.condomcas;;1;1
3;Condoms | Proportion of sexual acts in which condoms are used with regular partners;Programs/scenarios;M.condom.reg[:];sex.condomreg;;1;1
4;Acts | Number of sexual acts per person per year with commercial partners;Programs/scenarios;M.numacts.cas[:];sex.numactscas;;1;1
5;Acts | Number of sexual acts per person per year with casual partners;Programs/scenarios;M.numacts.com[:];sex.numactscom;;1;1
6;Acts | Number of sexual acts per person per year with regular partners;Programs/scenarios;M.numacts.reg[:];sex.numactsreg;;1;1
7;Circumcision | Proportion of males who are circumcised;Programs/scenarios;M.circum[:];sex.circum;;1;1
8;Circumcision | Number of medical male circumcisions performed per year;Programs/scenarios;M.numcircum[:];sex.numcircum;;1;1
9;STI | Prevalence of ulcerative STIs;Programs/scenarios;M.stiprevulc[:];epi.stiprevulc;;1;1
10;STI | Prevalence of discharging STIs;Programs/scenarios;M.stiprevdis[:];epi.stiprevdis;;1;1
11;Testing | Proportion of people who are tested for HIV each year;Programs/scenarios;M.hivtest[:];txrx.hivtest;;1;1
12;Testing | Proportion of PLHIV aware of their HIV status;Programs/scenarios;M.propaware[:];txrx.hivtest;;1;1
13;Treatment | Number of PLHIV on ART;Programs/scenarios;M.txtotal;txrx.numfirstline;;1;
14;Treatment | Proportion of PLHIV on ART;Programs/scenarios;M.txtotal;txrx.numfirstline;;1;
15;Treatment | CD4-based ART eligibility criterion;Programs/scenarios;M.txelig;txrx.txelig;;1;
16;PrEP | Proportion of risk encounters covered by PrEP;Programs/scenarios;M.prep[:];txrx.prep;;1;1
17;Injecting drug use | Number of injections per person per year;Programs/scenarios;M.numacts.inj[:];inj.numinject;;1;1
18;Injecting drug use | Proportion of injections using receptively shared needle-syringes;Programs/scenarios;M.sharing[:,:];inj.sharing;;1;1
19;Injecting drug use | Proportion of people on OST;Programs/scenarios;M.numost;inj.numost;;1;
20;Injecting drug use | Number of people on OST;Programs/scenarios;M.numost;inj.numost;;1;
21;PMTCT | Proportion of pregnant women receiving Option B/B+;Programs/scenarios;M.numpmtct;txrx.numpmtct;;1;
22;PMTCT | Number of pregnant women receiving Option B/B+;Programs/scenarios;M.numpmtct;txrx.numpmtct;;1;
23;PMTCT | Proportion of mothers who breastfeed;Programs/scenarios;M.breast;txrx.breast;;1;
1;Mortality | HIV-related mortality rate (AIDS stage);Manual calibration;M.const.death.aids;const.death.aids;1;;
2;Efficacy | Per-exposure efficacy of medical male circumcision;Manual calibration;M.const.eff.circ;const.eff.circ;1;;
3;Efficacy | Per-exposure efficacy of condoms;Manual calibration;M.const.eff.condom;const.eff.condom;1;;
4;Efficacy | Transmission-related behavior change following diagnosis;Manual calibration;M.const.eff.dx;const.eff.dx;1;;
5;Injecting drug use | Reduction in risk-related injecting frequency for people on OST;Manual calibration;M.const.eff.ost;const.eff.ost;1;;
6;PMTCT | Relative transmission probability under option B/B+;Manual calibration;M.const.eff.pmtct;const.eff.pmtct;1;;
7;Transmission | HIV transmission cofactor increase due to ulcerative STIs;Manual calibration;M.const.eff.sti;const.eff.sti;1;;
8;Transmission | HIV transmission cofactor decrease due to virally suppressive ART;Manual calibration;M.const.eff.tx;const.eff.tx;1;;
9;Treatment failure | Failure rate per year for first-line ART;Manual calibration;M.const.fail.first;const.fail.first;1;;
10;Treatment failure | Failure rate per year for subsequent lines of ART;Manual calibration;M.const.fail.second;const.fail.second;1;;
11;Per-exposure HIV transmission probability for injection with a contaminated needle-syringe;Manual calibration;M.const.trans.inj;const.trans.inj;1;;
12;Per-exposure HIV transmission probability for penile-vaginal insertive intercourse;Manual calibration;M.const.trans.mfi;const.trans.mfi;1;;
13;Per-exposure HIV transmission probability for penile-vaginal receptive intercourse;Manual calibration;M.const.trans.mfr;const.trans.mfr;1;;
14;Per-exposure HIV transmission probability for penile-anal insertive intercourse;Manual calibration;M.const.trans.mmi;const.trans.mmi;1;;
15;Per-exposure HIV transmission probability for penile-anal receptive intercourse;Manual calibration;M.const.trans.mmr;const.trans.mmr;1;;
""" 

def maybe_bool(p):
    if p in ['0','1']: p = bool(int(p))
    return p

fields = {1:"name", 5:"calibration", 6:"modifiable"}
model_key_field = 3
input_key_field = 4
dims = {None:0,':':1,':,:':2} #scalar, 1-dim and 2-dim array

def parameters():
    import re
    lines = [l.strip() for l in ALL_PARAMETERS_SOURCE.split('\n')][2:-1]
    split_lines = [l.split(';') for l in lines]
    result = []
    for line in split_lines:
        entry = {}
        for key in fields:
            item = line[key]
            if key in (5, 6) and item=='': # boolean parameter or nothing
                item='0'
            entry[fields[key]] = maybe_bool(item)
        param, pops = re.match('M\.([^[]+)(?:\[(.+?)\])?',line[model_key_field]).groups()
        entry['keys']=param.split('.')
        entry['dim'] = dims[pops]
        input_info = line[input_key_field]
        valid_input_info = re.match('[^-]+', input_info)
        input_keys = []
        page = None
        if valid_input_info:
            input_info_keys = re.split('[^a-z\.]', input_info)
            for key in input_info_keys:
                page, input_key = re.match('([^.]+?)\.(.+)', key).groups() # assume all keys have the same page :-}
                input_keys.append(input_key)
        entry['page'] = page
        entry['input_keys']=input_keys
        result.append(entry)
    return result

parameter_list = parameters()

def input_parameter(input_key):
    entry = [param for param in parameter_list if input_key in param['input_keys']]
    if entry:
        return entry[0]
    else:
        return None

def input_parameters(input_key):
    return [param for param in parameter_list if input_key in param['input_keys']]

def input_parameter_name(input_key):
    param = input_parameter(input_key)
    if param:
        return param['name']
    else:
        return None

def parameter_name(key): #params is the output of parameters() method
    if not type(key)==list: key=[key]
    entry = [param for param in parameter_list if ''.join(param['keys'])==''.join(key)]
    if entry:
        return entry[0]['name']
    else:
        return None


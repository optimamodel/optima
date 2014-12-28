ALL_PARAMETERS_SOURCE = \
"""
Parameter name;Description;Manual calibration?;Available in scenarios;Example sheet & row;Input page.parameter;Notes;
M.aidstest;AIDS testing rate per person per year;1;1;='Testing & Treatment'!W14;txrx.aidstest;;
M.circum[:];Circumcision probability;0;1;='Sexual behavior'!W69:W74;sex.circum;;
M.condom.cas[:];Condom usage probability, casual partnerships;1;1;='Sexual behavior'!W47:W52;sex.condomcas;;
M.condom.com[:];Condom usage probability, commercial partnerships;1;1;='Sexual behavior'!W58:W63;sex.condomcom;;
M.condom.reg[:];Condom usage probability, regular partnerships;1;1;='Sexual behavior'!W36:W41;sex.condomreg;;
M.const.cd4trans.acute;Relative HIV transmissibility, acute stage;1;0;='Constants'!C15;const.cd4trans.acute;;
M.const.cd4trans.aids;Relative HIV transmissibility, AIDS stage;1;0;='Constants'!C19;const.cd4trans.aids;;
M.const.cd4trans.gt200;Relative HIV transmissibility, CD4>200 stage;1;0;='Constants'!C18;const.cd4trans.gt200;These could be consolidated. We need to handle transmission and viral load better;
M.const.cd4trans.gt350;Relative HIV transmissibility, CD4>350 stage;1;0;='Constants'!C17;const.cd4trans.gt350;;
M.const.cd4trans.gt500;Relative HIV transmissibility, CD4>500 stage;1;0;='Constants'!C16;const.cd4trans.gt500;;
M.const.death.acute;HIV-related mortality rate, acute stage;1;0;='Constants'!C49;const.death.acute;;
M.const.death.aids;HIV-related mortality rate, acute stage;1;0;='Constants'!C53;const.death.aids;;
M.const.death.gt200;HIV-related mortality rate, CD4>200 stage;1;0;='Constants'!C52;const.death.gt200;These could be consolidated. We need to handle death better;
M.const.death.gt350;HIV-related mortality rate, CD4>350 stage;1;0;='Constants'!C51;const.death.gt350;;
M.const.death.gt500;HIV-related mortality rate, CD4>500 stage;1;0;='Constants'!C50;const.death.gt500;;
M.const.death.tb;TB-related mortality rate;0;0;='Constants'!C55;const.death.tb;;
M.const.death.treat;Mortality rate while on treatment;1;0;='Constants'!C54;const.death.treat;;
M.const.eff.circ;Per-act efficacy of circumcision;1;0;='Constants'!C62;const.eff.circ;;
M.const.eff.condom;Per-act efficacy of condoms;1;0;='Constants'!C61;const.eff.condom;;
M.const.eff.dx;Diagnosis-related behavior change efficacy;1;0;='Constants'!C63;const.eff.dx;;
M.const.eff.meth;Sharing rate reduction from methadone;1;0;='Constants'!C65;const.eff.meth;;
M.const.eff.pmtct;Per-birth efficacy of PMTCT;1;0;='Constants'!C66;const.eff.pmtct;;
M.const.eff.sti;STI-related transmission increase;1;0;='Constants'!C64;const.eff.sti;;
M.const.eff.tx;Treatment-related transmission decrease;1;0;='Constants'!C67;const.eff.tx;Near the top;
M.const.fail.first;First-line ART failure rate;1;0;='Constants'!C42;const.fail.first;;
M.const.fail.second;Second-line ART failure rate;1;0;='Constants'!C43;const.fail.second;Just have one rate;
M.const.prog.acute;Progression rate from acute to CD4>500 stage;1;0;='Constants'!C25;const.prog.acute;;
M.const.prog.gt200;Progression rate from CD4>200 to AIDS stage;1;0;='Constants'!C28;const.prog.gt200;;
M.const.prog.gt350;Progression rate from CD4>350 to CD4>200 stage;1;0;='Constants'!C27;const.prog.gt350;;
M.const.prog.gt500;Progression rate from CD4>500 to CD4>350 stage;1;0;='Constants'!C26;const.prog.gt500;;
M.const.recov.gt200;Treatment recovery rate from AIDS to CD4>200 stage;1;0;='Constants'!C36;const.recov.gt200;;
M.const.recov.gt350;Treatment recovery rate from CD4>200 to CD4>350 stage;1;0;='Constants'!C35;const.recov.gt350;;
M.const.recov.gt500;Treatment recovery rate from CD4>350 to CD4>500 stage;1;0;='Constants'!C34;const.recov.gt500;;
M.const.trans.inj;Absolute per-act transmissibility of injection;1;0;='Constants'!C7;const.trans.inj;;
M.const.trans.mfi;Absolute per-act transmissibility of male-female insertive intercourse;1;0;='Constants'!C3;const.trans.mfi;;
M.const.trans.mfr;Absolute per-act transmissibility of male-female receptive intercourse;1;0;='Constants'!C4;const.trans.mfr;;
M.const.trans.mmi;Absolute per-act transmissibility of male-male insertive intercourse;1;0;='Constants'!C5;const.trans.mmi;;
M.const.trans.mmr;Absolute per-act transmissibility of male-male receptive intercourse;1;0;='Constants'!C6;const.trans.mmr;;
M.const.trans.mtctbreast;Absolute per-child transmissibility with breastfeeding;1;0;='Constants'!C8;const.trans.mtctbreast;;
M.const.trans.mtctnobreast;Absolute per-child transmissibility without breastfeeding;1;0;='Constants'!C9;const.trans.mtctnobreast;;
M.death[:];Background death rates;1;1;='Other epidemiology'!W3:W8;epi.death;;
M.hivtest[:];HIV testing rates;1;1;='Testing & Treatment'!W3:W8;txrx.hivtest;;
M.numacts.cas[:];Number of acts per person per year, casual;0;1;='Sexual behavior'!W14:W19;sex.numactscas;;
M.numacts.com[:];Number of acts per person per year, commercial;0;1;='Sexual behavior'!W25:W30;sex.numactscom;;
M.numacts.inj[:];Number of injections per person per year;0;1;='Injecting behavior'!W3:W8;inj.numinject;;
M.numacts.reg[:];Number of acts per person per year, regular;0;1;='Sexual behavior'!W3:W8;sex.numactsreg;;
M.numcircum;Number of circumcisions performed per year;0;1;='Sexual behavior'!W80:W85;sex.numcircum;;
M.numost;Number of people on OST;0;1;='Injecting behavior'!W20;inj.numost;;
M.numpmtct;Number of women on PMTCT;0;1;='Testing & Treatment'!W54;txrx.numpmtct;;
M.popsize[:];Total population size;1;0;Not modifiable;key.popsize;Ahhh, it should be modifiable! Huge uncertainty in this!;
M.pep;PEP prevalence;0;1;='Testing & Treatment'!W43:W48;txrx.pep;;
M.prep;PrEP prevalence;0;1;='Testing & Treatment'!W32:W37;txrx.prep;;
M.pships.cas[:,:];Matrix of casual partnerships;0;0;Not modifiable;pships.cas;;
M.pships.com[:,:];Matrix of commercial partnerships;0;0;Not modifiable;pships.com;;
M.pships.inj[:,:];Matrix of injecting partnerships;0;0;Not modifiable;pships.inj;;
M.pships.reg[:,:];Matrix of regular partnerships;0;0;Not modifiable;pships.reg;;
M.sharing;Needle-syringe sharing rate;1;1;='Injecting behavior'!W14;inj.sharing;;
M.stiprevdis[:];Discharging STI prevalence;1;1;='Other epidemiology'!W25:W30;epi.stiprevdis;;
M.stiprevulc[:];Ulcerative STI prevalence;1;1;='Other epidemiology'!W14:W19;epi.stiprevulc;;
M.transit.asym[:,:];Matrix of population transitions without replacement (e.g. aging);0;0;Not modifiable;transit.asym;;
M.transit.sym[:,:];Matrix of population transitions with replacement (e.g. KAPs);0;0;Not modifiable;transit.sym;;
M.tx1;Number of people on 1st-line treatment;0;1;='Testing & Treatment'!W20;txrx.numfirstline;;
M.tx2;Number of people on 2nd-line treatment;0;1;='Testing & Treatment'!W26;txrx.numsecondline;;
""" 

def maybe_bool(p):
    if p in ['0','1']: p = bool(int(p))
    return p

fields = {1:"name", 2:"calibration", 3:"modifiable"}
model_key_field = 0
input_key_field = 5
dims = {None:0,':':1,':,:':2} #scalar, 1-dim and 2-dim array

def parameters():
    import re
    lines = [l.strip() for l in ALL_PARAMETERS_SOURCE.split('\n')][2:-1]
    split_lines = [l.split(';') for l in lines]
    result = []
    for line in split_lines:
        entry = dict([(fields[key], maybe_bool(line[key]) ) for key in fields])
        param, pops = re.match('M\.([^[]+)(?:\[(.+?)\])?',line[model_key_field]).groups()
        entry['keys']=param.split('.')
        entry['dim'] = dims[pops]
        page, input_key = re.match('([^.]+?)\.(.+)', line[input_key_field]).groups()
        entry['page'] = page
        entry['input_key']=input_key
        result.append(entry)
    return result

parameter_list = parameters()

def input_parameter(input_key):
    entry = [param for param in parameter_list if param['input_key']==input_key]
    if entry:
        return entry[0]
    else:
        return None

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


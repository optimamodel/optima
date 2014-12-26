ALL_PARAMETERS_SOURCE = \
"""
Parameter name;Description;Manual calibration?;Modifiable?;Example sheet & row;Notes;
M.aidstest;AIDS testing rate per person per year;1;1;='Testing & Treatment'!W14;;
M.circum[:];Circumcision probability;0;1;='Sexual behavior'!W69:W74;;
M.condom.cas[:];Condom usage probability, casual partnerships;1;1;='Sexual behavior'!W47:W52;;
M.condom.com[:];Condom usage probability, commercial partnerships;1;1;='Sexual behavior'!W58:W63;;
M.condom.reg[:];Condom usage probability, regular partnerships;1;1;='Sexual behavior'!W36:W41;;
M.const.cd4trans.acute;Relative HIV transmissibility, acute stage;1;0;='Constants'!C15;;
M.const.cd4trans.aids;Relative HIV transmissibility, AIDS stage;1;0;='Constants'!C19;;
M.const.cd4trans.gt200;Relative HIV transmissibility, CD4>200 stage;1;0;='Constants'!C18;These could be consolidated. We need to handle transmission and viral load better;
M.const.cd4trans.gt350;Relative HIV transmissibility, CD4>350 stage;1;0;='Constants'!C17;;
M.const.cd4trans.gt500;Relative HIV transmissibility, CD4>500 stage;1;0;='Constants'!C16;;
M.const.death.acute;HIV-related mortality rate, acute stage;1;0;='Constants'!C49;;
M.const.death.aids;HIV-related mortality rate, acute stage;1;0;='Constants'!C53;;
M.const.death.gt200;HIV-related mortality rate, CD4>200 stage;1;0;='Constants'!C52;These could be consolidated. We need to handle death better;
M.const.death.gt350;HIV-related mortality rate, CD4>350 stage;1;0;='Constants'!C51;;
M.const.death.gt500;HIV-related mortality rate, CD4>500 stage;1;0;='Constants'!C50;;
M.const.death.tb;TB-related mortality rate;0;0;='Constants'!C55;;
M.const.death.treat;Mortality rate while on treatment;1;0;='Constants'!C54;;
M.const.eff.circ;Per-act efficacy of circumcision;1;0;='Constants'!C62;;
M.const.eff.condom;Per-act efficacy of condoms;1;0;='Constants'!C61;;
M.const.eff.dx;Diagnosis-related behavior change efficacy;1;0;='Constants'!C63;;
M.const.eff.ost;Sharing rate reduction from methadone;1;0;='Constants'!C65;;
M.const.eff.pmtct;Per-birth efficacy of PMTCT;1;0;='Constants'!C66;;
M.const.eff.sti;STI-related transmission increase;1;0;='Constants'!C64;;
M.const.eff.tx;Treatment-related transmission decrease;1;0;='Constants'!C67;Near the top;
M.const.fail.first;First-line ART failure rate;1;0;='Constants'!C42;;
M.const.fail.second;Second-line ART failure rate;1;0;='Constants'!C43;Just have one rate;
M.const.prog.acute;Progression rate from acute to CD4>500 stage;1;0;='Constants'!C25;;
M.const.prog.gt200;Progression rate from CD4>200 to AIDS stage;1;0;='Constants'!C28;;
M.const.prog.gt350;Progression rate from CD4>350 to CD4>200 stage;1;0;='Constants'!C27;;
M.const.prog.gt500;Progression rate from CD4>500 to CD4>350 stage;1;0;='Constants'!C26;;
M.const.recov.gt200;Treatment recovery rate from AIDS to CD4>200 stage;1;0;='Constants'!C36;;
M.const.recov.gt350;Treatment recovery rate from CD4>200 to CD4>350 stage;1;0;='Constants'!C35;;
M.const.recov.gt500;Treatment recovery rate from CD4>350 to CD4>500 stage;1;0;='Constants'!C34;;
M.const.trans.inj;Absolute per-act transmissibility of injection;1;0;='Constants'!C7;;
M.const.trans.mfi;Absolute per-act transmissibility of male-female insertive intercourse;1;0;='Constants'!C3;;
M.const.trans.mfr;Absolute per-act transmissibility of male-female receptive intercourse;1;0;='Constants'!C4;;
M.const.trans.mmi;Absolute per-act transmissibility of male-male insertive intercourse;1;0;='Constants'!C5;;
M.const.trans.mmr;Absolute per-act transmissibility of male-male receptive intercourse;1;0;='Constants'!C6;;
M.const.trans.mtctbreast;Absolute per-child transmissibility with breastfeeding;1;0;='Constants'!C8;;
M.const.trans.mtctnobreast;Absolute per-child transmissibility without breastfeeding;1;0;='Constants'!C9;;
M.death[:];Background death rates;1;1;='Other epidemiology'!W3:W8;;
M.hivtest[:];HIV testing rates;1;1;='Testing & Treatment'!W3:W8;;
M.numacts.cas[:];Number of acts per person per year, casual;0;1;='Sexual behavior'!W14:W19;;
M.numacts.com[:];Number of acts per person per year, commercial;0;1;='Sexual behavior'!W25:W30;;
M.numacts.inj[:];Number of injections per person per year;0;1;='Injecting behavior'!W3:W8;;
M.numacts.reg[:];Number of acts per person per year, regular;0;1;='Sexual behavior'!W3:W8;;
M.numcircum;Number of circumcisions performed per year;0;1;='Sexual behavior'!W80:W85;;
M.numost;Number of people on OST;0;1;='Injecting behavior'!W20;;
M.numpmtct;Number of women on PMTCT;0;1;='Testing & Treatment'!W54;;
M.popsize[:];Total population size;1;0;Not modifiable;Ahhh, it should be modifiable! Huge uncertainty in this!;
M.pep;PEP prevalence;0;1;='Testing & Treatment'!W43:W48;;
M.prep;PrEP prevalence;0;1;='Testing & Treatment'!W32:W37;;
M.pships.cas[:,:];Matrix of casual partnerships;0;0;Not modifiable;;
M.pships.com[:,:];Matrix of commercial partnerships;0;0;Not modifiable;;
M.pships.inj[:,:];Matrix of injecting partnerships;0;0;Not modifiable;;
M.pships.reg[:,:];Matrix of regular partnerships;0;0;Not modifiable;;
M.sharing;Needle-syringe sharing rate;1;1;='Injecting behavior'!W14;;
M.stiprevdis[:];Discharging STI prevalence;1;1;='Other epidemiology'!W25:W30;;
M.stiprevulc[:];Ulcerative STI prevalence;1;1;='Other epidemiology'!W14:W19;;
M.transit.asym[:,:];Matrix of population transitions without replacement (e.g. aging);0;0;Not modifiable;;
M.transit.sym[:,:];Matrix of population transitions with replacement (e.g. KAPs);0;0;Not modifiable;;
M.tx1;Number of people on 1st-line treatment;0;1;='Testing & Treatment'!W20;;
M.tx2;Number of people on 2nd-line treatment;0;1;='Testing & Treatment'!W26;;
""" 

def maybe_bool(p):
    if p in ['0','1']: p = bool(int(p))
    return p

def parameters():
    lines = [l.strip() for l in ALL_PARAMETERS_SOURCE.split('\n')][2:-1]
    split_lines = [l.split(';') for l in lines]
    return [{'keys':r[0].replace('[:]','').replace('[:,:]','').split('.')[1:],'name':r[1], 'modifiable':maybe_bool(r[3])} for r in split_lines]

def parameter_name(params, key):
    if not type(key)==list: key=[key]
    entry = [param for param in params if ''.join(param['keys'])==''.join(key)]
    if entry:
        return entry[0]['name']
    else:
        return None

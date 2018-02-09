library(plyr)
library(tidyverse)
library(stringr)
library(arm)
library(msm)

#############
##FUNCTIONS##
#############

#imputations#
impute <- function(i, data, newvar, inputs) {
  ivs <- colnames(coef(inputs))[-1]
  fix.coefs <- coef(inputs)[i,]
  random.u <- sigma.hat(inputs)[i]
  data$intercept <- 1
  ivs <- c("intercept",ivs)
  upper.bound <- ifelse(str_detect(newvar, ".pc"), 1, Inf)
  data[,newvar] <- rtnorm(dim(data)[1], 
                       as.matrix(data[,ivs]) %*% fix.coefs, random.u,
                                         lower=0, upper=upper.bound)
  data$intercept <- NULL
  data[,c("county","precinct","psid",newvar)]
}

#summary stats#
stats <- function(x, random.order, total.districts) {
  x$turnout.var <- x[,grep(".t.est", names(x))]
  x$percent.var <- x[,grep(".pc.est", names(x))]
  n <- dim(x)[1]
  x <- x[random.order,]
  x$district <- rep(1, n)*c(1:total.districts)
  x <- ddply(x, .(district), summarize,
             v=sum(turnout.var*percent.var)/sum(turnout.var),
             s=as.integer(v>=0.5))
  output <- data.frame(v=mean(x$v), s=mean(x$s), eg=(mean(x$s)-0.5)-2*(mean(x$v)-0.5),
                       comp=mean(x$v<0.55 & x$v>0.45))
}

#clean up numbers#
number.clean <- function(char.vector) {
  output <- str_trim(char.vector) %>% str_replace_all("%", "") %>%
    str_replace_all("\\$", "") %>% str_replace_all(",", "")
}

#race transformations#
party.pc <- function(var.root, d) {
  names2 <- names(d)
  vars <- names2[str_detect(names2, paste0(var.root, "[.]([d r])"))]
  if(length(vars)>1) {
    dem <- vars[str_detect(vars, paste0(var.root, ".d"))]
    rep <- vars[str_detect(vars, paste0(var.root, ".r"))]
    d[,paste0(var.root, ".t")] <- d[,dem] + d[,rep]
    d[,paste0(var.root, ".pc")] <- d[,dem]/(d[,dem] + d[,rep])
  }
  return(d)
}

#race transformations#
party.pc <- function(var.root, d) {
  names2 <- names(d)
  vars <- names2[str_detect(names2, paste0(var.root, "[.]([d r])"))]
  if(length(vars)>1) {
    dem <- vars[str_detect(vars, paste0(var.root, ".d"))]
    rep <- vars[str_detect(vars, paste0(var.root, ".r"))]
    d[,paste0(var.root, ".t")] <- d[,dem] + d[,rep]
    d[,paste0(var.root, ".pc")] <- d[,dem]/(d[,dem] + d[,rep])
    select <- (d[,paste0(var.root, ".pc")] == 1) | (d[,paste0(var.root, ".pc")] == 0)
    select[is.na(select)] <- FALSE
    d[select,paste0(var.root, ".pc")] <- NA
    select <- is.na(d[,paste0(var.root, ".pc")])
    d[select,paste0(var.root, ".t")] <- NA
  }
  return(d)
}

##############
##FORMATTING##
##############

setwd("/Users/ericmcghee/Dropbox/Redistricting/PlanScore/Data")

var.names <- read.csv("NC Variable names.csv", header=F, stringsAsFactors=F)

d <- read.csv("North Carolina Precinct-Level Results - 2016-11-08 General.csv",
              header=T, stringsAsFactors=F)
names(d) <- var.names[,2]
start <- which(names(d)=="nhw")
end <- dim(d)[2]
d[,start:end] <- sapply(d[,start:end], number.clean) %>% sapply(as.numeric) #formatting numbers
names <- names(d) %>% .[str_detect(., "[.]([d r])")] %>% #rename vars
  str_replace("[.]([d r])", "") %>% unique(.)
for(i in 1:length(names)) { #calculate proportions for every race
  d <- party.pc(names[i], d)
}
d <- mutate(d, nhw=nhw/100,
            coll=coll/100) %>%
  filter(!is.na(us.pres.pc), !is.na(nhw), !is.na(coll))

############
##ANALYSIS##
############

##US House##
#turnout#
model <- lm(us.hse.t ~ us.pres.t, data=d)
random.coefs <- sim(model, 1000)
output1 <- lapply(1:1000, function(w,x,y,z) impute(w,x,y,z), d, "us.hse.t.est", random.coefs)

turnout <- Reduce(function(x,y) merge(x, y, by=c("county","precinct","psid")), output1)
write.csv(turnout, "NC Precinct Model.US House.turnout.csv")

#dem proportion#
model <- lm(us.hse.pc ~ us.pres.pc + nhw + coll, data=d)
random.coefs <- sim(model, 1000)
output2 <- lapply(1:1000, function(w,x,y,z) impute(w,x,y,z), d, "us.hse.pc.est", random.coefs)
imputes <- lapply(1:1000, function(i) 
  merge(output1[[i]], output2[[i]], by=c("county","precinct","psid")))
proportion <- Reduce(function(x,y) merge(x, y, by=c("county","precinct","psid")), output2)
write.csv(proportion, "NC Precinct Model.US House.propD.csv")

scramble <- sample(1:dim(imputes[[1]])[1], dim(imputes[[1]])[1]) #for random districts

#votes, seats, eg for random districts#
sv <- ldply(lapply(imputes, function(x,y,z) stats(x,y,z), scramble, 13))
results.ushse <- data.frame(V=round(median(sv$v),3),V.moe=round(2*sd(sv$v),3),
                          S=round(median(sv$s),3),S.moe=round(2*sd(sv$s),3),
                          EG=round(median(sv$eg),3),EG.moe=round(2*sd(sv$eg),3),
                          Competitive=round(median(sv$comp),3),
                          Competitive.moe=round(2*sd(sv$comp),3))

#other models of dem proportion#
model <- lm(us.hse.pc ~ us.pres.pc, data=d)
summary(model)

model <- lm(us.hse.pc ~ us.pres.pc + us.sen.pc + nc.gov.pc, data=d)
summary(model)

model <- lm(us.hse.pc ~ us.pres.pc + us.sen.pc + nc.gov.pc + nhw + coll, data=d)
summary(model)

model <- lmer(us.hse.pc ~ us.pres.pc + us.sen.pc + nc.gov.pc + nhw + coll +
                (1|county), data=d)
display(model)

model <- lm(us.hse.pc ~ us.pres.pc + us.sen.pc + nc.ag.pc + nc.aud.pc + nc.agr.pc +
              nc.ins.pc + nc.lab.pc + nc.gov.pc + nc.lg.pc + nc.ss.pc + nc.spi.pc +
              nc.trs.pc + nhw + coll + medinc, data=d)
summary(model)

##NC Leg House##

#model with pres vote + census only#
#turnout#
model <- lm(nc.hse.t ~ us.pres.t, data=d)
random.coefs <- sim(model, 1000)
output1 <- lapply(1:1000, function(w,x,y,z) impute(w,x,y,z), d, "nc.hse.t.est", random.coefs)

turnout <- Reduce(function(x,y) merge(x, y, by=c("county","precinct","psid")), output1)
write.csv(turnout, "NC Precinct Model.NC House.turnout.csv")

#dem proportion#
model <- lm(nc.hse.pc ~ us.pres.pc + nhw + coll, data=d)
random.coefs <- sim(model, 1000)
output2 <- lapply(1:1000, function(w,x,y,z) impute(w,x,y,z), d, "nc.hse.pc.est", random.coefs)
imputes <- lapply(1:1000, function(i) 
  merge(output1[[i]], output2[[i]], by=c("county","precinct")))
proportion <- Reduce(function(x,y) merge(x, y, by=c("county","precinct","psid")), output2)
write.csv(proportion, "NC Precinct Model.NC House.propD.csv")

scramble <- sample(1:dim(imputes[[1]])[1], dim(imputes[[1]])[1]) #for random districts

#votes, seats, eg for random districts#
sv <- ldply(lapply(imputes, function(x,y,z) stats(x,y,z), scramble, 120))
results.nchse <- data.frame(V=round(median(sv$v),3),V.moe=round(2*sd(sv$v),3),
                          S=round(median(sv$s),3),S.moe=round(2*sd(sv$s),3),
                          EG=round(median(sv$eg),3),EG.moe=round(2*sd(sv$eg),3),
                          Competitive=round(median(sv$comp),3),
                          Competitive.moe=round(2*sd(sv$comp),3))

#other models of dem proportion#
model <- lm(nc.hse.pc ~ us.pres.pc, data=d)
summary(model)

model <- lm(nc.hse.pc ~ us.pres.pc + us.sen.pc + nc.gov.pc, data=d)
summary(model)

model <- lm(nc.hse.pc ~ us.pres.pc + us.sen.pc + nc.gov.pc + nhw + coll, data=d)
summary(model)
plot(d$us.pres.t[!is.na(d$nc.hse.pc)], model$residuals)

model <- lmer(nc.hse.pc ~ us.pres.pc + us.sen.pc + nc.gov.pc + nhw + coll +
                (1|county), data=d)
display(model)

model <- lm(nc.hse.pc ~ us.pres.pc + us.sen.pc + nc.ag.pc + nc.aud.pc + nc.agr.pc +
              nc.ins.pc + nc.lab.pc + nc.gov.pc + nc.lg.pc + nc.ss.pc + nc.spi.pc +
              nc.trs.pc + nhw + coll + medinc, data=d)
summary(model)

##NC Leg Senate##
#model with pres vote + census only#
#turnout#
model <- lm(nc.sen.t ~ us.pres.t, data=d)
random.coefs <- sim(model, 1000)
output1 <- lapply(1:1000, function(w,x,y,z) impute(w,x,y,z), d, "nc.sen.t.est", random.coefs)

turnout <- Reduce(function(x,y) merge(x, y, by=c("county","precinct","psid")), output1)
write.csv(turnout, "NC Precinct Model.NC Senate.turnout.csv")

#dem proportion#
model <- lm(nc.sen.pc ~ us.pres.pc + nhw + coll, data=d)
random.coefs <- sim(model, 1000)
output2 <- lapply(1:1000, function(w,x,y,z) impute(w,x,y,z), d, "nc.sen.pc.est", random.coefs)
imputes <- lapply(1:1000, function(i) 
  merge(output1[[i]], output2[[i]], by=c("county","precinct")))
proportion <- Reduce(function(x,y) merge(x, y, by=c("county","precinct","psid")), output2)
write.csv(proportion, "NC Precinct Model.NC Senate.propD.csv")

scramble <- sample(1:dim(imputes[[1]])[1], dim(imputes[[1]])[1]) #for random districts

#votes, seats, eg for random districts#
sv <- ldply(lapply(imputes, function(x,y,z) stats(x,y,z), scramble, 50))
results.ncsen <- data.frame(V=round(median(sv$v),3),V.moe=round(2*sd(sv$v),3),
                      S=round(median(sv$s),3),S.moe=round(2*sd(sv$s),3),
                      EG=round(median(sv$eg),3),EG.moe=round(2*sd(sv$eg),3),
                      Competitive=round(median(sv$comp),3),
                      Competitive.moe=round(2*sd(sv$comp),3))

#other models of dem proportion#
model <- lm(nc.sen.pc ~ us.pres.pc, data=d)
summary(model)

model <- lm(nc.sen.pc ~ us.pres.pc + us.sen.pc + nc.gov.pc, data=d)
summary(model)

model <- lm(nc.sen.pc ~ us.pres.pc + us.sen.pc + nc.gov.pc + nhw + coll, data=d)
summary(model)
plot(d$us.pres.t[!is.na(d$nc.sen.pc)], model$residuals)

model <- lmer(nc.sen.pc ~ us.pres.pc + us.sen.pc + nc.gov.pc + nhw + coll +
                (1|county), data=d)
display(model)

model <- lm(nc.sen.pc ~ us.pres.pc + us.sen.pc + nc.ag.pc + nc.aud.pc + nc.agr.pc +
              nc.ins.pc + nc.lab.pc + nc.gov.pc + nc.lg.pc + nc.ss.pc + nc.spi.pc +
              nc.trs.pc + nhw + coll + medinc, data=d)
summary(model)

##combining all the results##
results <- rbind(results.nchse, results.ncsen, results.ushse)
rownames(results) <- c("NC House", "NC Senate", "US House")
print(results)


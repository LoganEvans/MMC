# Copyright (c) 2014, Logan P. Evans <loganpevans@gmail.com>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

library("TTR")
library("ff")
library("ffbase")
library("graphics")

hit_rate = function(vec, filter) {
  (cumsum(vec$hit[]) / seq_along(vec$row[]))[c(rep(FALSE, filter), TRUE)]
}

draw_ts_comparison = function(mmc, arc, lru, mmc_rw, min_, suffix, filter=1) {
  fname = sprintf("../media/ts_%s.pdf", sub("^([^.]*).*", "\\1", suffix))
  pdf(fname)
  ratio = 1 / (length(mmc[[1]]) / 20)
  len = length(mmc[[1]])
  n = len / 15
  #ratio = 1 / 5000

  min_ts = SMA(min_$hit[], n=n)[c(rep(FALSE, filter), TRUE)]
  mmc_ts = SMA(mmc$hit[], n=n)[c(rep(FALSE, filter), TRUE)]
  lru_ts = SMA(lru$hit[], n=n)[c(rep(FALSE, filter), TRUE)]
  arc_ts = SMA(arc$hit[], n=n)[c(rep(FALSE, filter), TRUE)]
  mmc_rw_ts = SMA(mmc_rw$hit[], n=n)[c(rep(FALSE, filter), TRUE)]

  xlim=c(1, length(mmc_ts[]))
  ylim=c(min(min_ts, mmc_ts, lru_ts, arc_ts, na.rm=TRUE),
         max(min_ts, mmc_ts, lru_ts, arc_ts, na.rm=TRUE))

  plot.ts(
      min_ts, xlim=xlim, ylim=ylim, col="black",
      xlab="Request Number", ylab="EMA Hit Rate",
      axes=FALSE
      #main=sub("^([^.]*).*", "\\1", suffix)
      )
  axis(
      side=1,
      labels=formatC(seq.int(0, len + 1, length.out=5), format="d"),
      at=seq(0, length(mmc_ts[]), length.out=5))
  axis(side=2)
  box()

  lines.ts(hit_rate(min_, filter), xlim=xlim, ylim=ylim, col="black", lty=2)

  lines.ts(
      lru_ts, xlim=xlim, ylim=ylim, col="darkgreen")
  lines.ts(hit_rate(lru, filter), xlim=xlim, ylim=ylim, col="darkgreen", lty=2)

  lines.ts(
      arc_ts, xlim=xlim, ylim=ylim, col="red")
  lines.ts(hit_rate(arc, filter), xlim=xlim, ylim=ylim, col="red", lty=2)

  lines.ts(
      mmc_ts, xlim=xlim, ylim=ylim, col="blue")
  lines.ts(hit_rate(mmc, filter), xlim=xlim, ylim=ylim, col="blue", lty=2)

  lines.ts(
      mmc_rw_ts, xlim=xlim, ylim=ylim, col="purple")
  lines.ts(hit_rate(mmc_rw, filter), xlim=xlim, ylim=ylim, col="purple", lty=2)

  legend(
      "topleft", col=c("black", "blue", "purple", "red", "darkgreen"),
      legend=c("MIN", "MMC", "MMC (RW)", "ARC", "LRU"), lty = c(1, 1, 1, 1, 1),
      bg="white")

  dev.off()
}

get_csv = function(fname) {
  read.csv.ffdf(file=sprintf("csv/%s", fname), header=TRUE, VERBOSE=TRUE,
                first.rows=10000, next.rows=50000)
}

draw_dump = function(tag, request_number, value_contour) {
  png(sprintf("../media/frames/cache_dump_image_%s_%07d.png", tag, as.integer(request_number)))
  info_file = read.csv(
      sprintf("csv/cache_dump/cache_dump_info__%s_%07d.csv", tag, as.integer(request_number)),
      header=T)
  cache = read.csv(
      sprintf("csv/cache_dump/cache_dump__%s_%07d.csv", tag, as.integer(request_number)),
      header=T)

  colorp = colorRampPalette(
      c("green", "red"), space="Lab",
      length(cache[[1]]))(length(cache[[1]]))
  plot(
      xlab="Rank", ylab="Depth",
      cache$rank[], cache$depth[],
      col=colorp[cache$value_order[]],
      cex=0.75, pch=16,
      xlim=c(0, 1000), ylim=c(0, 1000))

  points(
      cache$rank[!!cache$is_evicted[]],
      cache$depth[!!cache$is_evicted[]],
      col='black', bg=colorp[cache$value_order[!!cache$is_evicted[]]],
      cex=0.75, pch=21,
      xlim=c(0, 1000), ylim=c(0, 1000))
  dev.off()
}

draw_ev = function(ev, suffix) {
  fname = sprintf("../media/ev_%s.png", sub("^([^.]*).*", "\\1", suffix))
  #pdf(fname)
  png(fname, width=800, height=800)
  plot(ev$rank[], ev$depth[], col="#00000008", cex=0.01,
       xlab="Rank", ylab="Depth")
  dev.off()
}

draw_tau = function(mmc, suffix) {
  fname = sprintf("../media/tau_%s.png", sub("^([^.]*).*", "\\1", suffix))
  png(fname)
  plot.ts(mmc$tau[], xlab="Request Number", ylab="tau")
  dev.off()
}

draw_tau_and_theta = function(mmc, tag, filter) {
  fname = sprintf("../media/tau_and_theta_%s.pdf", sub("^([^.]*).*", "\\1", tag))
  len = length(mmc[[1]])
  ylim = c(0, max(max(mmc$depth[]), max(mmc$rank[])))
  pdf(fname)
  par(mar=c(5, 4, 4, 5) + 0.1)
  plot.ts(
      1 / mmc$theta1[c(rep(FALSE, filter), TRUE)], ylim=ylim, col="red",
      xlab="Request Number", ylab="Average Measurement",
      axes=FALSE)
  axis(
      side=1,
      labels=formatC(seq.int(0, len + 1, length.out=5), format="d"),
      at=seq(0, length(mmc$theta1[c(rep(FALSE, filter), TRUE)][]), length.out=5))
  axis(side=2)
  box()

  lines(1 / mmc$theta0[c(rep(FALSE, filter), TRUE)], ylim=c(0, 2000), col="blue")

  par(new=T, mar=c(5, 4, 4, 5) + 0.1)
  plot.ts(
      mmc$tau[c(rep(FALSE, filter), TRUE)],
      ylim=c(0, 1), xlab="", ylab="", yaxt='n',
      axes=FALSE)
  axis(side=4)
  mtext(parse(text="tau[1]"), side=4, line=3)

  leg = parse(text=c("frac(1, theta[1])", "frac(1, theta[2])", "tau[1]"))
  legend(
      "topleft", bg="white", legend=leg, col=c("blue", "red", "black"),
      lty=c(1, 1, 1))
  dev.off()
}

tags = c(
  "445_445_1780_2",
  "600_600_2400_2",
  "1000_1000_4000_2",

  "445_445_1780_3",
  "600_600_2400_3",
  "1000_1000_4000_3",

  "445_445_1780_4",
  "600_600_2400_4",
  "1000_1000_4000_4",

  "445_445_1780_5"
)

tag = tags[7]
filter=500

#tag = "1000_1000_4000_4"
if (0) {
  for (tag in tags) {
    mmc = get_csv(sprintf("mmc_%s.csv", tag))
    mmc_rw = get_csv(sprintf("mmc_rw_%s.csv", tag))
    arc = get_csv(sprintf("arc_%s.csv", tag))
    lru = get_csv(sprintf("lru_%s.csv", tag))
    min_ = get_csv(sprintf("min_%s.csv", tag))
    draw_ts_comparison(mmc, arc, lru, mmc_rw, min_, tag, filter=filter)
  }
}
#draw_ts_comparison(mmc, arc, lru, suffix)

if (0) {
    ev = get_csv(sprintf("mmc_evict_%s.csv", tag))
    draw_dump(tag, 1000, mean(ev$value[]))
}

if (1) {
  for (i in 1:10000) {
    draw_dump(tag, i)
  }
}

if (0) {
  for (tag in tags) {
    ev = get_csv(sprintf("mmc_evict_%s.csv", tag))
    draw_ev(ev, tag)
  }
}

if (0) {
  for (tag in tags) {
    ev = get_csv(sprintf("mmc_rw_evict_%s.csv", tag))
    draw_ev(ev, sprintf("rw_%s", tag))
  }
}

if (0) {
  for (tag in tags) {
    mmc = get_csv(sprintf("mmc_%s.csv", tag))
    draw_tau_and_theta(mmc, tag, filter)
  }
}


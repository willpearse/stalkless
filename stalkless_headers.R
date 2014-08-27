#Recode JPEG loading to ignore 'stalked' ones
# - this needs re-writing so it doesn't pre-allocated and is optimised...
# - I'm loathe to do that here, as this is a very minor modification of the original Momocs code!
import.img.Conte.stalkless <- function (img, x, auto = TRUE, plot = TRUE, max.iter=10000) 
{
  if (missing(x)) {
    if (auto) {
      x <- round(dim(img)/2)
    }
    else {
      x <- c(1, 1)
    }
  }
  if (img[x[1], x[2]] != 0) {
    return(NA)
  }
  while (abs(img[x[1], x[2]] - img[x[1], (x[2] - 1)]) < 0.1) {
    x[2] <- x[2] - 1
  }
  a <- 1
  M <- matrix(c(0, -1, -1, -1, 0, 1, 1, 1, 1, 1, 0, -1, -1, 
                -1, 0, 1), 2, 8, byrow = TRUE)
  M <- cbind(M[, 8], M, M[, 1])
  X <- 0
  Y <- 0
  x1 <- x[1]
  x2 <- x[2]
  SS <- NA
  S <- 6
  while ((any(c(X[a], Y[a]) != c(x1, x2)) | length(X) < 3)) {
    if(a > max.iter) return(NA)
    if (abs(img[x[1] + M[1, S + 1], x[2] + M[2, S + 1]] - 
              img[x[1], x[2]]) < 0.1) {
      a <- a + 1
      X[a] <- x[1]
      Y[a] <- x[2]
      x <- x + M[, S + 1]
      SS[a] <- S + 1
      S <- (S + 7)%%8
    }
    else if (abs(img[x[1] + M[1, S + 2], x[2] + M[2, S + 
                                                    2]] - img[x[1], x[2]]) < 0.1) {
      a <- a + 1
      X[a] <- x[1]
      Y[a] <- x[2]
      x <- x + M[, S + 2]
      SS[a] <- S + 2
      S <- (S + 7)%%8
    }
    else if (abs(img[x[1] + M[1, S + 3], x[2] + M[2, S + 
                                                    3]] - img[x[1], x[2]]) < 0.1) {
      a <- a + 1
      X[a] <- x[1]
      Y[a] <- x[2]
      x <- x + M[, S + 3]
      SS[a] <- S + 3
      S <- (S + 7)%%8
    }
    else {
      S <- (S + 1)%%8
    }
  }
  return(cbind((Y[-1]), ((dim(img)[1] - X))[-1]))
}

import.jpg.stalkless <- function (jpg.list) 
{
  cat("Extracting", length(jpg.list), ".jpg outlines...\n")
  if (length(jpg.list) > 10) {
    pb <- txtProgressBar(1, length(jpg.list))
    t <- TRUE
  }
  else {
    t <- FALSE
  }
  res <- list()
  for (i in seq(along = jpg.list)) {
    img <- import.img.prepare(jpg.list[i])
    res[[i]] <- import.img.Conte.stalkless(img)
    if (t) 
      setTxtProgressBar(pb, i)
  }
  names(res) <- substr(jpg.list, start = 1, stop = nchar(jpg.list) - 
                         4)
  return(res)
}

check.images <- function(image.files, nb.h=32){
  good.files <- rep(FALSE, length(image.files))
  for(i in seq_along(image.files)){
    try({
      eFourier(Coo(image.files[i]), nb.h=32)
      good.files[i] <- TRUE
    }, silent=TRUE)
  }
  return(image.files[good.files])
}

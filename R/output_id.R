id <- '12345'
base.message <- base::message
base.cat <- base::cat
base.print <- base::print
base.print.default <- base::print.default

id.message <- function(...) {
  base.cat(paste0('#', id, '#'))
  base.message(...)
}
unlockBinding('message', as.environment('package:base'))
assign('message', id.message, getNamespace('base'))

id.cat <- function(...) {
  base.cat(paste0('#', id, '#'))
  base.cat(...)
}
unlockBinding('cat', as.environment('package:base'))
assign('cat', id.cat, getNamespace('base'))

id.print <- function(...) {
  base.cat(paste0('#', id, '#'))
  base.print(...)
}
unlockBinding('print', as.environment('package:base'))
assign('print', id.print, getNamespace('base'))

id.print.default <- function(...) {
  base.cat(paste0('#', id, '#'))
  base.print.default(...)
}
unlockBinding('print.default', as.environment('package:base'))
assign('print.default', id.print.default, getNamespace('base'))

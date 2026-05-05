# -*- coding: utf-8 -*-
import logging
import urllib.request
import urllib.parse
import json

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import get_slot_value
from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ← Cambia esto por tu URL de ngrok cada vez que la arranques
API_BASE_URL = "https://resigned-certify-shakiness.ngrok-free.dev"


def obtener_datos_pelicula(titulo):
    """
    Llama a la API Flask y devuelve el diccionario con los datos
    de la película, o None si hay error.
    """
    titulo_encoded = urllib.parse.quote(titulo)
    url = f"{API_BASE_URL}/pelicula?titulo={titulo_encoded}"
    
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AlexaSkill/1.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            datos = json.loads(response.read().decode("utf-8"))
            if "error" in datos:
                return None
            return datos
    except Exception as e:
        logger.error(f"Error llamando a la API: {e}")
        return None


# ── HANDLERS ──────────────────────────────────────────────────────────────────

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = (
            "Bienvenido a datos de películas. "
            "Puedes preguntarme por la nota, el director, la sinopsis, "
            "la duración o el número de votos de una película."
        )
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Por ejemplo, puedes decir: ¿cuál es la nota de Interstellar?")
                .response
        )


class NotaIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("NotaIntent")(handler_input)

    def handle(self, handler_input):
        movie_name = get_slot_value(handler_input=handler_input, slot_name="movie")
        datos = obtener_datos_pelicula(movie_name)

        if datos and datos.get("rating"):
            speak_output = f"La nota de {datos['title']} en IMDb es {datos['rating']} sobre 10."
        else:
            speak_output = f"No he podido obtener la nota de {movie_name}."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("¿Quieres saber algo más de alguna película?")
                .response
        )


class DirectorIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("DirectorIntent")(handler_input)

    def handle(self, handler_input):
        movie_name = get_slot_value(handler_input=handler_input, slot_name="movie")
        datos = obtener_datos_pelicula(movie_name)

        if datos and datos.get("director"):
            speak_output = f"{datos['title']} está dirigida por {datos['director']}."
        else:
            speak_output = f"No he podido obtener el director de {movie_name}."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("¿Quieres saber algo más de alguna película?")
                .response
        )


class SinopsisIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("SinopsisIntent")(handler_input)

    def handle(self, handler_input):
        movie_name = get_slot_value(handler_input=handler_input, slot_name="movie")
        datos = obtener_datos_pelicula(movie_name)

        if datos and datos.get("synopsis"):
            speak_output = f"La sinopsis de {datos['title']} es: {datos['synopsis']}"
        else:
            speak_output = f"No he podido obtener la sinopsis de {movie_name}."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("¿Quieres saber algo más de alguna película?")
                .response
        )


class DuracionIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("DuracionIntent")(handler_input)

    def handle(self, handler_input):
        movie_name = get_slot_value(handler_input=handler_input, slot_name="movie")
        datos = obtener_datos_pelicula(movie_name)

        if datos and datos.get("duration"):
            speak_output = f"{datos['title']} tiene una duración de {datos['duration']}."
        else:
            speak_output = f"No he podido obtener la duración de {movie_name}."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("¿Quieres saber algo más de alguna película?")
                .response
        )


class VotosIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("VotosIntent")(handler_input)

    def handle(self, handler_input):
        movie_name = get_slot_value(handler_input=handler_input, slot_name="movie")
        datos = obtener_datos_pelicula(movie_name)

        if datos and datos.get("votes"):
            votos = f"{int(datos['votes']):,}".replace(",", ".")
            speak_output = f"{datos['title']} tiene {votos} votos en IMDb."
        else:
            speak_output = f"No he podido obtener los votos de {movie_name}."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("¿Quieres saber algo más de alguna película?")
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = (
            "Puedes preguntarme cosas como: ¿qué nota tiene Interstellar?, "
            "¿quién dirige Dune?, ¿cuánto dura El Padrino?, "
            "¿cuál es la sinopsis de Matrix?, o ¿cuántos votos tiene Oppenheimer?"
        )
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("¿Qué película quieres consultar?")
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
            ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)
        )

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Hasta luego.").response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = (
            "No he entendido eso. Puedes preguntarme por la nota, el director, "
            "la sinopsis, la duración o los votos de una película."
        )
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Prueba con: ¿qué nota tiene Interstellar?")
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        return (
            handler_input.response_builder
                .speak("Ha ocurrido un error. Inténtalo otra vez.")
                .ask("Puedes volver a preguntarme por una película.")
                .response
        )


# ── REGISTRO ──────────────────────────────────────────────────────────────────

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(NotaIntentHandler())
sb.add_request_handler(DirectorIntentHandler())
sb.add_request_handler(SinopsisIntentHandler())
sb.add_request_handler(DuracionIntentHandler())
sb.add_request_handler(VotosIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()